// DevFlow Skill Sync Script
// Keeps Codex SKILL.md in sync with Claude Code _SKILL.md
// Usage: node scripts/sync-skills.js [--reverse]

const fs = require('fs');
const path = require('path');

const skillsDir = path.join(__dirname, '..', 'skills');
const isReverse = process.argv.includes('--reverse');

function syncSkill(skillName) {
    const dir = path.join(skillsDir, skillName);
    const claudeFile = path.join(dir, '_SKILL.md');
    const codexFile = path.join(dir, 'SKILL.md');

    if (!fs.existsSync(claudeFile) && !fs.existsSync(codexFile)) return;

    if (isReverse) {
        if (fs.existsSync(codexFile)) {
            const content = fs.readFileSync(codexFile, 'utf-8');
            fs.writeFileSync(claudeFile, content);
            console.log('[reverse] ' + skillName + '/_SKILL.md <- SKILL.md');
        }
    } else {
        if (fs.existsSync(claudeFile)) {
            let content = fs.readFileSync(claudeFile, 'utf-8');
            content = content.split('\n')
                .filter(line => !line.trimStart().startsWith('allowed-tools:'))
                .join('\n');
            fs.writeFileSync(codexFile, content);
            console.log('[forward] ' + skillName + '/SKILL.md <- _SKILL.md');
        }
    }
}

const skillNames = fs.readdirSync(skillsDir).filter(f =>
    fs.statSync(path.join(skillsDir, f)).isDirectory()
);

console.log('Syncing ' + skillNames.length + ' skills...');
skillNames.forEach(syncSkill);
console.log('Done.');
