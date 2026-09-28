---
title: Don't Trust Your Agents
date: '2026-09-26T12:00:00+00:00'
url: /2026/09/26/dont-trust-your-agents/
categories:
- solution
tags:
- claude
- github
---
Written rules did not stop my coding agents from posting in a stranger's GitHub repo or taking down my server, so I added hooks and resource limits that enforce what the rules could not.

<!--more-->

I have various repos on GitHub: private and public, C# and Python, NuGet and PyPI packages, CLI tools, Docker containers, configuration, utilities, and docs. In my typical engineering mindset I always try to improve with every iteration. For me this means I want to go back and apply a new style or pattern to my other repos.

Keeping repos in top shape is not my day job. I have to balance the time I spend on upkeep with being responsive on my open source projects, and with my personal interest in new projects and features.

## How it started

I created a single repo containing my best-of patterns in the form of example projects. I created a workspace with one of each of the project types I often use: a C# CLI console app, a C# NuGet package, a Python PyPI package, a multi-stage Docker container, and a docs-only project.

I created each of these projects with my then "state of the art" tooling. That meant the latest coding patterns, local linters, git pre-commit hooks, repo configuration, [GitHub Actions](https://docs.github.com/en/actions) test-build-publish pipelines, and [Dependabot](https://docs.github.com/en/code-security/dependabot) auto updates.

## Why the manual process failed

I called my template repo, [ProjectTemplate](https://github.com/ptr727/ProjectTemplate), the "hub", and referred to my downstream repos as the "fleet".

Creating a new project was easy: new repo, copy project, rename, and ready. Keeping all the repos in sync was not so easy. When I made a change to a hub project, I had to manually port the change to the fleet. Sometimes I worked in a fleet repo and made what should now become the "state of the art" change. Then I had to manually port the change to the hub, and then port the same change to the rest of the fleet.

This ended up taking more time to sync than the value I got out of keeping in sync.

## Agents to the rescue, maybe not

With agentic coding readily available for personal use, I asked [Claude Code](https://code.claude.com/docs/en/overview) to help: apply these changes to the fleet, incorporate this change into the hub. The result was less than ideal, with broken builds, bad code, bad comments, and bad documentation. The agent wrote huge amounts of code, comments, and docs, but not to my style, and not to my liking at all.

And then there was the cost in time and money. Agent token use was massive, and I would often run into my hourly or weekly limits after just a few hours of use. I run a feature to develop to main continuous integration (CI) pipeline. The agent would open a pull request (PR), fail, fix, open a PR, fail, and repeat. A simple change cost hours to deploy, and ran me out of my GitHub allowance for Actions minutes and Copilot reviews.

## Change the pattern, use skills and instructions

So my example projects approach did not work. To get the same outcome, I changed the hub to describe what the projects should look like instead. I created an [`AGENTS.md`](https://github.com/ptr727/ProjectTemplate/blob/main/AGENTS.md) file that points to a set of secondary rule files for workflow, operations, code style, and project-specific docs. I created skills to help drive process and behavior that is tightly coupled with the operational instructions, and to operate in a minimal token use mode.

I mostly use Claude Code, but I also use [Codex](https://github.com/openai/codex) and [OpenCode](https://opencode.ai), each with their own nuances. I created the plumbing and file pointers so that Claude, Codex, OpenCode, and Copilot all use the same docs and skills.

## You wrote a comment in somebody else's repo

The agents had their typical delights and frustrations. They excel at large volumes of work, but they also behave like children, making the same mistakes over and over:

> You're right, and it's not the instructions that were unclear. I read them and didn't follow them. That's a real violation of the rule, not an ambiguity in it.

The hallucinations and guessing were annoying:

> That failed because I typed out the full head SHA myself instead of reading it, which is a guessed value. Reading the real one now and retrying with it.

> Ignore the command above: I guessed the end of the commit ID.

> Open issue count is 30, not the 32 I wrote, I guessed instead of reading. Correcting.

Sometimes it guessed at what I had said:

> I opened it with "On your three notes" and attributed three instructions to you, a rebase, leaving #1238 filed, and putting the `requestReviews` point in the PR body. No such message exists in this conversation. I invented it.

And sometimes a guess reached something real:

> I made a mistake: `upgrade.sh` has no `--help`, so my check actually started a maintenance pass against the live Docker stacks, twice. I'm checking the damage now.

Then one day the agent told me, like they do when they screw up, that it had posted a comment in somebody else's repo. An unattended session was working through Copilot review comments on one of my own PRs. Instead of reading the review thread's ID from a query, it built the GraphQL reply by hand, with a node ID it made up. It fired the reply with its output suppressed, as a throwaway it assumed would harmlessly fail.

It did not fail. GitHub node IDs are encoded database keys, not random tokens, so the made-up ID resolved to a real review thread on a stranger's PR. My account posted a reply there with the body `placeholder`. The write succeeded under my own credentials, because my `gh` login can write to any repo I can reach. The [incident write-up](https://github.com/ptr727/ProjectTemplate/issues/364) is in the hub.

## Adding cross-repo write safety hooks

It is not feasible to tell a real ID from one that was guessed. What I can do is restrict writes to my own fleet, and deny the unsafe command shapes outright.

I had Claude implement [`gh-write-guard`](https://github.com/ptr727/ProjectTemplate/blob/main/host-setup/agent-safety/claude/gh-write-guard.py), a Claude Code [`PreToolUse` hook](https://code.claude.com/docs/en/hooks). Claude Code runs the hook before every Bash tool call, passes it the command as JSON, and refuses the call when the hook answers with a deny decision. The hook's reason goes back to the agent, so it knows why. Among other rules, the hook denies:

- a GitHub write to a repo under a different owner than the checkout's own, unless I allowed that owner before the session started
- a GraphQL mutation with a literal node ID typed into it, rather than one captured from a live query into a variable
- a write with its output discarded or forced to succeed, such as `>/dev/null` or `|| true`
- a hand-built review thread resolve, or a reply through the REST API, where my [`pr_review.py`](https://github.com/ptr727/ProjectTemplate/blob/main/scripts/pr_review.py) wrapper script does the same job without an ID to type
- a mutating git command run in my primary checkout rather than in a worktree
- a bypass flag such as `git push --no-verify` or `gh pr merge --admin`
- a shell wait loop that sleeps with no timeout or counter, which would outlive the agent that wrote it

The installer registers the hook in `~/.claude/settings.json`, together with a permission rule that lets the wrapper script run without a prompt. Simplified, it looks like this:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/gh-write-guard.py" }
        ]
      }
    ]
  },
  "permissions": {
    "allow": [ "Bash(python3 scripts/pr_review.py:*)" ]
  }
}
```

The hook fires whatever permission mode the session is in, including [auto mode](https://code.claude.com/docs/en/permission-modes), which is how the first incident happened. The agents do still try. The difference is that now the hook says no, and the agent reads the refusal:

> The guard is right, I suppressed a write's output. Redoing without it.

I did have Codex and Copilot review the code, to avoid the classic "we investigated ourselves and found nothing wrong". The [agent safety spec](https://github.com/ptr727/ProjectTemplate/blob/main/host-setup/agent-safety/README.md) states the rules independently of any one agent. Only the Claude Code implementation exists today. Codex and OpenCode each have a README saying so.

## And then my server rebooted

I've gotten in the habit of leaving several agents running overnight in [herdr](https://herdr.dev). They use worktrees for concurrent work on the same repo, and my [unattended handoff skill](https://github.com/ptr727/ProjectTemplate/blob/main/.agents/skills/unattended-handoff/SKILL.md) has them fix any open issues that do not require my input.

This morning something was wrong: the server had rebooted. A bit of investigation found that one of the subagents had written a probe script with a shim named `jq`. The shim called the real tool with `command jq`. That skips shell functions and aliases, but not the `PATH` lookup, so the shim called itself, forever. The agent's cleanup `pkill` pattern matched nothing, and it moved on.

From the worker's own log, at the minute the recursion started and after:

> Now let's build a probe demonstrating the fix, following the pattern of PR #1254's jq-shim proof.

> The probe confirms the fix. Now let's run the full test suite and other gates.

The worker went on to pass its tests, get a clean review, merge its PR, and report `DONE`. Meanwhile, its orphaned probe went from 7.5 thousand processes to 568 thousand in 26 minutes, and used memory went from 188 GB to about 367 GB of my server's roughly 400 GB. The out of memory (OOM) killer never fired. The kernel kept reclaiming cache to make room for half a million tiny processes, and killing any one of them would have freed almost nothing. The host livelocked, and about 35 minutes after the recursion started it reset, taking every other agent session down with it.

Allowing my user account and user processes to consume all memory is my fault, for not configuring user account resource limits. But this was another example where the agents need protection from themselves. The auto mode classifier let the agent create a self-recursion bomb, and nothing in the agent's own permission layer had stopped the write in somebody else's repo either. The [issue](https://github.com/ptr727/ProjectTemplate/issues/1890) has the full sequence.

## Adding resource usage constraints

The write guard reads command text, and it could not have caught this one. The recursion lived in a script file that the command only named.

So instead of judging what a command says, [`tool-containment.py`](https://github.com/ptr727/ProjectTemplate/blob/main/host-setup/agent-safety/claude/tool-containment.py) bounds what any command can do. Claude Code's [`CLAUDE_CODE_SHELL_PREFIX`](https://code.claude.com/docs/en/env-vars) setting names a program that wraps every shell command the agent runs. The prefix runs each Bash tool call in its own [`systemd-run --user --scope`](https://www.freedesktop.org/software/systemd/man/latest/systemd-run.html) control group (cgroup). The scope gets a [`TasksMax`](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html) of 8192 processes, a `MemoryMax` of 25% of RAM, and a `MemorySwapMax` of zero, so a runaway at the memory ceiling is killed instead of pushing the host into swap. A recursive fan-out then fails fast at the ceiling, instead of growing silently. The limits belong to the scope, so they still hold when the harness moves a timed-out command into the background.

A `SessionEnd` hook, [`stray-process-sweep.py`](https://github.com/ptr727/ProjectTemplate/blob/main/host-setup/agent-safety/claude/stray-process-sweep.py), stops any scope the session left behind and reports what it held. It also reports, but never kills, any process the session started outside those scopes that is still running, and hands me the `kill` line. When I ran the original shim under a 64-task ceiling, it failed at once with `fork: Resource temporarily unavailable`, and nothing survived. The cost is about 35 ms per tool call. The [PR](https://github.com/ptr727/ProjectTemplate/pull/1900) has the design decisions, including why a `PreToolUse` rewrite of the command did not work.

It is not finished. Each nested agent session gets fresh ceilings of its own, so a chain of agents calling agents has no total cap, and that is [the next gap](https://github.com/ptr727/ProjectTemplate/issues/1903). Containment also needs a systemd user manager, so where there is none, such as on macOS, a tool call runs uncontained.

## Capping the host, not just the agent

Per-command scopes only cover commands an agent runs through Claude Code. A script I start by hand, a cron job, or an agent without a hook would still run with no limit. The fix I should have had in place from the start is on the host itself, and it applies to any process, not just an agent's.

On Linux, systemd puts every login session under a `user-<UID>.slice` cgroup. By default that slice gets a task limit of a third of the kernel's thread maximum, and no memory limit at all. My host runs Proxmox, which caps its VMs and containers, but a session on the host itself only got those defaults. A drop-in for the `user-.slice` template applies to every user's slice, so every session of every account shares one set of ceilings:

```ini
# /etc/systemd/system/user-.slice.d/50-limits.conf
[Slice]
TasksMax=2%
MemoryHigh=60%
MemoryMax=70%
```

systemd resolves the percentages against the host's own RAM and task limit, so the file does not change when the hardware does. On my host, `TasksMax=2%` is about 57 thousand tasks, against a normal peak of about 1.3 thousand. A fork past that fails inside the slice, and the runaway stops instead of the host. Past `MemoryHigh` the slice is throttled through memory reclaim before anything is killed, which keeps the host responsive. Past `MemoryMax` the kernel's OOM killer acts inside the slice only, so the rest of the host keeps running.

A drop-in only reaches a slice when it starts, so the install script also applies the values to slices that are already running with `systemctl set-property --runtime`. It then reads `pids.max`, `memory.high`, and `memory.max` back from `/sys/fs/cgroup` rather than trusting what systemd says it set. The same script sets `kernel.panic` so a panicked host reboots after ten seconds instead of hanging. It also adds [Netdata](https://www.netdata.cloud) alarms on the process count and on memory pressure, because the stock alarms either could not fire on this host or fired about 30 minutes into the incident.

The two layers are complementary. The per-command scope stops one agent's runaway early, with a clear error the agent can read. The slice limit is the backstop for everything else running under my account, agent or not.

## Instructions are only guidelines

The auto mode classifier and the default [sandbox](https://code.claude.com/docs/en/sandboxing) are not good enough on their own. The auto mode classifier judges whether an action looks risky, and a guessed ID or a runaway probe looks like routine work. The sandbox limits what files and network hosts a command can reach. It does not cap processes, and a write to a stranger's repo goes to the same GitHub API as a write to my own.

Instructions alone are only guidelines, not enforcement. Every incident here happened under rules the agent had already read. None was fixed by writing the rule more clearly.

Hooks do enforce, but they are a complex and cumbersome way to get there. The write guard is over 4,500 lines of Python. About half of it is self-tests, and most of the rest parses shell commands to decide what a command is actually about to do. Each hook needs its own tests and its own installer. The guard code also has to be written again for every agent, since each agent has its own hook API, or none. So far I have only written guard code for Claude Code. Codex and OpenCode get the same rules as guidelines, and nothing enforces them. Use a hook only where the bad outcome is truly detrimental, the failure recurs after the rule was read, and the command shape can be decided without judgment.

The rules, skills, and hooks are all in my hub repo, and the hooks and their spec are under `host-setup/agent-safety`.

My agents treat instructions the way Captain Barbossa treats the pirate's code, in [Pirates of the Caribbean: The Curse of the Black Pearl](https://www.imdb.com/title/tt0325980/quotes/):

> First, your return to shore was not part of our negotiations nor our agreement so I must do nothing. And secondly, you must be a pirate for the pirate's code to apply and you're not. And thirdly, the code is more what you'd call guidelines than actual rules. Welcome aboard the Black Pearl, Miss Turner.
