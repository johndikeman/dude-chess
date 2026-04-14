---
name: agent-logs
description: Access and search agent logs from agent.log or via journalctl for the dude-chess service.
---

# Agent Logs

This skill provides access to the logs for the `dude-chess` service and instructions for restarting the service

## Accessing Logs

### Using journalctl

The agent runs as a user service named `dude-chess`. You can access the logs using `journalctl`:

```bash
journalctl --user -u dude-chess
```

To see the last 100 lines:
```bash
journalctl --user -u dude-chess -n 100
```

To follow the logs:
```bash
journalctl --user -u dude-chess -f
```

to restart the agent:

```
sudo systemctl --user restart dude-chess
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
