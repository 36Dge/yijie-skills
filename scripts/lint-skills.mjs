import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

const requiredSections = ["## 目标", "## 输入", "## 输出", "## 禁止行为", "## 审批要求", "## 评测标准"];

async function findSkillFiles(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await findSkillFiles(fullPath)));
    } else if (entry.name === "SKILL.md") {
      files.push(fullPath);
    }
  }
  return files;
}

const skillFiles = await findSkillFiles("plugins");
if (skillFiles.length === 0) {
  throw new Error("No SKILL.md files found.");
}

for (const file of skillFiles) {
  const content = await readFile(file, "utf8");
  const missing = requiredSections.filter((section) => !content.includes(section));
  if (missing.length > 0) {
    throw new Error(`${file} missing sections: ${missing.join(", ")}`);
  }
}

console.log(`Checked ${skillFiles.length} skill file(s).`);
