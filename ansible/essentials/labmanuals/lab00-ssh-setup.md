## SSH Key-Based Authentication – Ansible Lab

1. **Verify user**

   ```bash
   whoami
   ```

   Expected: `labuser`

2. **Generate SSH key pair**

   ```bash
   ssh-keygen -t rsa
   ```

   Press **Enter** for the default location and leave the passphrase empty.

3. **Create `.ssh` directory if required**

   ```bash
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   ```

4. **Copy the public key to `authorized_keys`**

   ```bash
   cp ~/.ssh/id_rsa.pub ~/.ssh/authorized_keys
   ```

5. **Set permissions**

   ```bash
   chmod 600 ~/.ssh/authorized_keys
   ```

6. **Test passwordless SSH**

   ```bash
   ssh labuser@localhost
   ```

   It should connect without asking for the `labuser` password.

7. **Create Ansible inventory**

   ```ini
   [webservers]
   web1 ansible_host=localhost ansible_user=labuser
   ```

8. **Test Ansible**

   ```bash
   ansible managed -i inventory -m ping
   ```

9. **Expected result**

   ```text
   managed1 | SUCCESS => {
       "changed": false,
       "ping": "pong"
   }
   ```

**Note:** `cp id_rsa.pub authorized_keys` is fine for a **single-key lab**. In a real environment with multiple authorized keys, use `cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys` so existing keys aren't overwritten.
