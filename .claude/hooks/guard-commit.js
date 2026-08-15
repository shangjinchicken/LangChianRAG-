// 守门员脚本：拦截 git commit，检查是否已通过单元测试 + 质量检查
// 触发时机：Claude Code 的 PreToolUse hook，在任何 Bash 工具调用前执行
// 逻辑：如果不是 git commit 命令 → 放行；是 → 检查两个"通过文件"是否有效
//   - 有效 → 放行（exit 0）
//   - 无效 → 拒绝（stdout 输出 deny JSON，reason 会被 Claude 看到，引导它去跑 /gitcommit）

const { execSync } = require('child_process')
const fs = require('fs')
const path = require('path')

const ROOT = path.resolve(__dirname, '..', '..')
const CHECK_DIR = path.join(ROOT, '.claude', 'checks')
const TESTER_PASS = path.join(CHECK_DIR, 'tester-pass.json')
const QUALITY_PASS = path.join(CHECK_DIR, 'quality-pass.json')

// 读 stdin，拿到 hook 传入的 JSON（含 tool_input.command）
function readStdin() {
  return new Promise((resolve) => {
    let data = ''
    process.stdin.on('data', (chunk) => { data += chunk })
    process.stdin.on('end', () => resolve(data))
  })
}

// 读通过文件，返回 null 表示文件不存在或格式错误
function readPassFile(file) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'))
  } catch {
    return null
  }
}

// 拿当前工作区的代码指纹
function currentFingerprint() {
  return execSync(`node "${path.join(CHECK_DIR, 'fingerprint.js')}"`, { cwd: ROOT })
    .toString('utf8').trim()
}

// 输出"拒绝"决策给 Claude Code
function deny(reason) {
  process.stdout.write(JSON.stringify({
    hookEventName: 'PreToolUse',
    hookSpecificOutput: {
      permissionDecision: 'deny',
      permissionDecisionReason: reason
    }
  }))
  process.exit(0)
}

async function main() {
  const input = await readStdin()
  let payload
  try {
    payload = JSON.parse(input)
  } catch {
    process.exit(0)  // 拿不到输入就放行，不误伤
  }

  const cmd = payload.tool_input?.command || ''
  // 判断是不是 git commit 命令（判断放脚本里，不依赖 hook 的 if 过滤）
  if (!/\bgit\s+commit\b/.test(cmd)) {
    process.exit(0)  // 不是 commit，放行
  }

  // 是 git commit，开始检查两个通过文件
  const tester = readPassFile(TESTER_PASS)
  const quality = readPassFile(QUALITY_PASS)

  const missing = []
  if (!tester) missing.push('单元测试')
  if (!quality) missing.push('质量检查')
  if (missing.length > 0) {
    deny(`提交被拦截：缺少${missing.join('、')}的通过记录。请先运行 /gitcommit 完成检查后再提交。`)
  }

  // 校验两个文件都是 passed 且指纹匹配当前代码
  const current = currentFingerprint()
  const stale = []
  if (!tester.passed) stale.push('单元测试（未通过）')
  else if (tester.fingerprint !== current) stale.push('单元测试（代码已改动，检查结果过期）')

  if (!quality.passed) stale.push('质量检查（未通过）')
  else if (quality.fingerprint !== current) stale.push('质量检查（代码已改动，检查结果过期）')

  if (stale.length > 0) {
    deny(`提交被拦截：${stale.join('、')}。请先运行 /gitcommit 重新检查后再提交。`)
  }

  // 全部通过，放行
  process.exit(0)
}

main()
