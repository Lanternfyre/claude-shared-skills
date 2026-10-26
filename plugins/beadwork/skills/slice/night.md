# Night compatibility

`night` means unattended availability. Use the same [slice loop](SKILL.md) and [session handoffs](sessions.md) as attended work. Queue questions for the operator and continue independent authorized work. Availability changes question delivery, not implementation authority or the ability to reuse a conversation.

`scripts/night-run.sh` remains a compatibility launcher for existing schedules. New runs use `scripts/run.py --mode unattended` with their authorized bead or queue. A schedule chooses when to launch; it is not part of the agent's decision-making process. Preserve project-specific unattended restrictions where they exist.
