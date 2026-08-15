// 工作区代码指纹计算脚本
// 用途：生成一串代表"当前代码内容"的哈希值。
// 只要任意受 git 跟踪（或未跟踪）的文件内容发生变化，这串哈希就会变。
// 它被三处共用，保证算法一致：
//   1. tester agent（写"测试通过文件"时记录指纹）
//   2. quality-engineer agent（写"质量通过文件"时记录指纹）
//   3. guard-commit.js（拦截 git commit 时，比对通过文件里的指纹是否还匹配当前代码）

const { execSync } = require('child_process')
const crypto = require('crypto')
const fs = require('fs')
const path = require('path')

// 项目根目录（脚本位置在 .claude/checks/ 下，往上两级就是根目录）
const ROOT = path.resolve(__dirname, '..', '..')

// 收集所有受 git 跟踪的文件 + 未跟踪的文件（--exclude-standard 会跳过 .gitignore 里的文件）
// 用 -z 分隔，避免文件名里带空格/中文时被截断
function listFiles() {
  const tracked = execSync('git ls-files -z', { cwd: ROOT, encoding: 'buffer' })
    .toString('utf8').split('\0').filter(Boolean)

  const untracked = execSync('git ls-files --others --exclude-standard -z', { cwd: ROOT, encoding: 'buffer' })
    .toString('utf8').split('\0').filter(Boolean)

  return [...new Set([...tracked, ...untracked])]
}

// 对每个文件内容算 SHA-1（和 git 的 hash-object 一致），再拼起来算总哈希
function computeFingerprint() {
  const files = listFiles().sort()  // 排序，保证顺序固定
  const hasher = crypto.createHash('sha1')

  for (const rel of files) {
    const abs = path.join(ROOT, rel)
    try {
      const content = fs.readFileSync(abs)
      hasher.update(rel)       // 文件名也参与哈希，防止文件重命名后误判
      hasher.update('\0')
      hasher.update(content)
      hasher.update('\0')
    } catch (e) {
      // 文件可能在读取瞬间被删除（比如正在被移动），跳过即可
    }
  }

  return hasher.digest('hex')
}

process.stdout.write(computeFingerprint())
