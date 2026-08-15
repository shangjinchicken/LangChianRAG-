// 清理脚本：git push 成功后，删除旧的"通行证"（通过文件）
// 触发时机：Claude Code 的 PostToolUse hook，在 Bash 工具调用完成后执行
// 逻辑：
//   - 不是 git push 命令 → 直接放行（exit 0，什么都不做）
//   - 是 git push → 判断是否推送成功 → 成功则删两个通过文件
//   - 始终 exit 0（PostToolUse 只负责清理，不拦截 push）

const { execSync } = require('child_process')
const fs = require('fs')
const path = require('path')

const ROOT = path.resolve(__dirname, '..', '..')

// 两个"通行证"文件的路径（tester 和 quality-engineer 各自写一个）
const PASS_FILES = [
  path.join(ROOT, '.claude', 'checks', 'tester-pass.json'),
  path.join(ROOT, '.claude', 'checks', 'quality-pass.json')
]

// 读 stdin，拿到 hook 传入的 JSON（含 tool_input.command）
function readStdin() {
  return new Promise((resolve) => {
    let data = ''
    process.stdin.on('data', (chunk) => { data += chunk })
    process.stdin.on('end', () => resolve(data))
  })
}

// 判断 push 是否成功：本地 HEAD 和上游 @{u} 一致，说明已经推上去了
// 不依赖 Claude Code 返回结果的格式，直接看 git 自己的状态，更可靠
function pushSucceeded() {
  try {
    // stdio 里把 stderr 设为 ignore，避免"没有上游"这类报错信息漏到终端
    const head = execSync('git rev-parse HEAD', { cwd: ROOT, stdio: ['ignore', 'pipe', 'ignore'] }).toString('utf8').trim()
    const upstream = execSync('git rev-parse @{u}', { cwd: ROOT, stdio: ['ignore', 'pipe', 'ignore'] }).toString('utf8').trim()
    return head === upstream
  } catch {
    // 取不到上游（没配远程、或命令失败）→ 视为"未确认推送成功"，保守处理不删
    return false
  }
}

// 删除两个通过文件；文件不存在就跳过，不影响正常流程
function deletePassFiles() {
  for (const file of PASS_FILES) {
    try {
      fs.unlinkSync(file)
    } catch {
      // 文件可能已经被删过（比如重复 push），删不到就跳过
    }
  }
}

async function main() {
  let payload
  try {
    payload = JSON.parse(await readStdin())
  } catch {
    process.exit(0)  // 拿不到输入就放行，不误伤
  }

  const cmd = payload.tool_input?.command || ''
  // 判断是不是 git push 命令（判断放脚本里，不依赖 hook 的 if 过滤）
  if (!/\bgit\s+push\b/.test(cmd)) {
    process.exit(0)  // 不是 push，不干任何事
  }

  // 是 push，且推送成功 → 删除旧通行证
  if (pushSucceeded()) {
    deletePassFiles()
  }

  process.exit(0)
}

main()
