---
name: agent-logs
description: Access and search agent logs from agent.log or via journalctl for the dude-agent service.
---

# Agent Logs

This skill provides access to the logs for the `dude-agent` service.

## Accessing Logs

### Using journalctl

The agent runs as a user service named `dude-agent`. You can access the logs using `journalctl`:

```bash
journalctl --user -u dude-agent
```

To see the last 100 lines:
```bash
journalctl --user -u dude-agent -n 100
```

To follow the logs:
```bash
journalctl --user -u dude-agent -f
```

### Using agent.log

If logs are redirected to a file, they might be in `agent.log` in the working directory:

```bash
tail -f agent.log
```

You can also search the logs:
```bash
grep "error" agent.log
```
