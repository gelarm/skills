> **Note:** This repository contains Gelarm's implementation of skills for GIMS (Gelarm Infrastructure Management System). For information about the Agent Skills standard, see [agentskills.io](http://agentskills.io).

# Skills
Skills are folders of instructions, scripts, and resources that coding agent loads dynamically to improve performance on specialized tasks. Skills teach coding agent how to complete specific tasks in a repeatable way, whether that's creating documents with your company's brand guidelines, analyzing data using your organization's specific workflows, or automating personal tasks.

# Try in Claude Code, Qwen Code, or Cursor

## Claude Code
You can register this repository as a Claude Code Plugin marketplace by running the following command in Claude Code:
```
/plugin marketplace add https://github.com/gelarm/skills.git
```

Then, to install a specific set of skills:
1. Select `Browse and install plugins`
2. Select `gims-agent-skills`
3. Select `gims-skills`
4. Select `Install now`

Alternatively, directly install either Plugin via:
```
/plugin install gims-skills@gims-agent-skills
```

## Qwen Code
Run Qwen Code:
```bash
qwen --experimental-skills
```

to use .qwen/skills
