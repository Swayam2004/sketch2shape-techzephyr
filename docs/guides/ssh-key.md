# SSH key for the shared GPU pod

Do this once. You need a key pair. The private half stays on your laptop. Only the public half (the `.pub` file) goes to Udit.

## 1. Check for an existing key

macOS Terminal

```
ls ~/.ssh/id_ed25519.pub
```

Windows PowerShell

```
Test-Path $env:USERPROFILE\.ssh\id_ed25519.pub
```

If the file exists, skip to step 3 and send that one. Do not overwrite it.

## 2. Make a key

macOS Terminal or Windows PowerShell

```
ssh-keygen -t ed25519 -C "s2s-yourname"
```

Press Enter to accept the default path. A passphrase is optional. If Windows says `ssh-keygen` is not found, open Settings, Optional features, and add "OpenSSH Client".

## 3. Print the public key

macOS

```
cat ~/.ssh/id_ed25519.pub
```

Windows PowerShell

```
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub
```

The output is one line that starts with `ssh-ed25519`. Send that whole line to Udit in chat. Never send the file named `id_ed25519` without `.pub`. That one is your private key.

## 4. Connect once Udit shares the pod address

Udit sends a command like this. Replace the key path for your OS.

macOS

```
ssh root@<POD_IP> -p <PORT> -i ~/.ssh/id_ed25519
```

Windows PowerShell

```
ssh root@<POD_IP> -p <PORT> -i $env:USERPROFILE\.ssh\id_ed25519
```

The first time, type `yes` when it asks to trust the host. You should land in a shell on the pod. Run `nvidia-smi` to see the GPU.

## If it fails

| Message | Cause and fix |
| --- | --- |
| `Permission denied (publickey)` | Udit has not added your key yet, or you pointed `-i` at the wrong file. Confirm the line he pasted matches your `.pub` file. |
| `Connection refused` or timeout | The pod is stopped, or the IP and port changed. Ask Udit for the current command. |
| `UNPROTECTED PRIVATE KEY FILE` on Windows | Rerun `ssh-keygen` into a new file, or ask your agent to fix the file permissions. |
| Host key changed warning | The pod was recreated. Remove the old line from `known_hosts` and reconnect. |

Your Claude Code agent can run these steps for you. Tell it "set up my SSH key from docs/guides/ssh-key.md" and paste only the public line when it asks.
