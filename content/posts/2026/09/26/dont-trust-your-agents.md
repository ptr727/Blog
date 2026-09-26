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
## Why it started

I have various repos on github, private, public, C#, nuget, Python, pypi, CLI, docker, config, utility, docs, etc.
In my typical engineering mindset I always try to improve with every iteration, and for me this means I want to go back and apply a new style or pattern to other repos.
Keeping repos in top shape is not my day job, and I have to balance the time I spend on upkeep with being responsive on open source projects with my personal new project or feature interests.

## How it started

I created a single repo containing my best-of patterns in the form of example projects. I created a workspace and one of each of the projects I often use, C# CLI console app, C# nuget package, Python PyPI package, multi-stage docker container, and a docs only project.
I created each of these projects with my then "state of the art" tooling, latest coding patterns, local linters, git pre-commit hooks, repo configuration, GitHub Actions test-build-publish pipelines, and dependabot auto updates.

## Why the manual process failed

I called my template repo the "hub", and referred to my downstream repos as the "fleet".
Creating a new project was easy, new repo, copy project, rename, and ready. But keeping all the repos in sync was not so easy. When I made a change to a hub project, I had to manually port the change to the fleet. When I worked in a fleet repo and made what should now become the "state of the art" change, I had to manually port the change to the hub and then port the same change to the rest of the fleet.
This ended up taking more time to sync than the value I got out of keeping in sync.

## Agents to the rescue, maybe not

With agentic coding being readily available for personal use, I asked Claude to help, apply these changes to the fleet, incorporate this change into the hub. The result was less than ideal, broken builds, bad code, bad comments, bad documentation. The agent was writing huge amounts of code and comments and docs, but not to my style, and not to my liking at all.
And then there was the cost in time and money. Massive agent token utilization, I would often run into my hourly or weekly limits after just a few hours of use. I run a feature to dev to main CI pipeline, and the agent would code PR, fail, fix, PR, fail, repeat, costing hours to deploy a simple change, and running me out of GitHub allowance for Actions hours and Copilot reviews.

## Change the pattern, use skills and instructions

So my example projects approach did not work, but to get the same outcome I changed the hub to become descriptive of what the projects should look like instead. I created an AGENTS.md file that points to a set of secondary rule files for workflow, operations, codestyle, and project specific docs. I created skills to help drive process and behavior that is tightly coupled with the operational instructions, and to operate in a minimal token use mode.
Although I mostly use Claude Code, I also use Codex and OpenCode, each with their own nuances, and I created the plumbing and file pointers so that the same docs and skills are used by Claude, Codex, OpenCode, and Copilot.

## What do you mean you wrote a comment in somebody else's repo?

The agents had their typical delights and frustrations, excel at large volumes of work, but also behave like children and making the same mistakes over and over. `You're right, and it's not the instructions that were unclear — I read them and didn't follow them. That's a real violation of the rule, not an ambiguity in it.`
And hallucinations and guessing that was annoying. `That failed because I typed out the full head SHA myself instead of reading it, which is a guessed value. Reading the real one now and retrying with it.`
and then one day the agent told me, like they do when they screw up, that it guessed a SHA and to see if it is writable they wrote a comment, in somebody else's repo. TODO: can we recover or guess the actual text from issue 364?

## Adding cross-repo write safety hooks

It is not feasible to distinguish a real SHA from one that was guessed, but I can restrict cross repo writes to only my fleet, and I can deny access to unsafe CLI tools.
I had Claude implement an agent hook (TODO, what do we call it?) that only allows mutations to my own repos, and only allows the use of specific tooling, my custom python wrapper script or specific `gh` CLI commands.
I did have Codex and Copilot review the code, to avoid the classic "we investigated ourselves and found nothing wrong".

## And then my server rebooted

I've gotten in the habit of leaving several agents running overnight in `herdr`, using worktrees for concurrent work on the same repo, and my unattended handoff skills to fix any open issues that do not require my input.
This morning something was wrong, the server rebooted, and a bit of investigation found that one of the subagents had recursively spawned hundreds of thousands of processes running my server's 348GB out and it OOM restarted.
Allowing my user account and user process to consume all memory is my fault for not configuring user account resource restrictions. But this was another example where the agents need protection from themselves, and as with the auto classifier allowing a write in somebody else's repo, the auto classifier allowed the agent to create a self recursion bomb. TODO get OOM details and wording from issue 1890.

## Adding resource usage constraints

TODO: Describe how the hook is implemented
