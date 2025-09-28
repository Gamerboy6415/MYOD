#!/bin/bash
set -euo pipefail
# ==============================================================================
# dasdec maker script thing
# ==============================================================================

MAIN_USER="main"
HOME_DIR="/home/${MAIN_USER}"

trap 'echo -e "\033[0;31mERROR: Script failed at line $LINENO\033[0m"' ERR

echo "--- Starting Installation ---"

echo "--> step 1: updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y


echo "--> step 2: installing required system packages..."
sudo apt-get install -y \
    xorg \
    python3-venv \
    python3-pip \
    python3 \
    multimon-ng \
    espeak-ng \
    pulseaudio \
    portaudio19-dev \
    ffmpeg \
    open-vm-tools-desktop

# ensure QuantumENDEC and dasdec are in the home directory
for folder in QuantumENDEC dasdec; do
    if [ ! -d "${HOME_DIR}/$folder" ]; then
        if [ -d "$folder" ]; then
            echo "--> Moving $folder to ${HOME_DIR}/"
            mv "$folder" "${HOME_DIR}/"
            chown -R ${MAIN_USER}:${MAIN_USER} "${HOME_DIR}/$folder"
        else
            echo "ERROR: $folder not found in current directory and not present in ${HOME_DIR}/"
            exit 1
        fi
    fi
done


# --- 3. set Up Project Files ---
PROJECT_DIR=$(pwd)
echo "--> step 3: Project located at ${PROJECT_DIR}"

# --- 4. create Python venv & install dependencies ---
# QuantumENDEC venv
echo "--> step 4a: Setting up QuantumENDEC venv (qevenv)..."
cd "${HOME_DIR}/QuantumENDEC"
python3 -m venv qevenv
source qevenv/bin/activate
pip install -r requirements.txt
deactivate

# dasdec venv
echo "--> step 4b: Setting up dasdec venv (venv)..."
cd "${HOME_DIR}/dasdec"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate

cd "${PROJECT_DIR}"




# --- 5. Apply System-Wide Audio & Video Fixes ---
echo "--> Step 5: Applying system permissions and audio stability fixes..."
# Add the current user to 'video' and 'audio' groups for hardware access
echo "--> Adding user to 'video' and 'audio' groups..."
sudo usermod -a -G video,audio $USER


# --- 6. Install endec user service ---
echo "--> step 6: Installing endec user service..."
mkdir -p "${HOME_DIR}/.config/systemd/user"
cat > "${HOME_DIR}/.config/systemd/user/endec.service" <<EOF
[Unit]
Description=ENDEC Service
After=network.target sound.target

[Service]
WorkingDirectory=${HOME_DIR}/QuantumENDEC
ExecStart=${HOME_DIR}/QuantumENDEC/start.sh
Restart=on-failure
RestartSec=10
Environment=XDG_RUNTIME_DIR=/run/user/1000

[Install]
WantedBy=default.target
PartOf=graphical-session.target
EOF

# chown -R ${MAIN_USER}:${MAIN_USER} "${HOME_DIR}/.config/systemd/user"

chmod +x "${HOME_DIR}/QuantumENDEC/start.sh"

systemctl --user daemon-reload
systemctl --user enable endec.service


# --- 7. Configure Auto-Login and Auto-Start ---
CURRENT_USER=$USER
echo "--> step 7: Configuring system to auto-login user '${CURRENT_USER}' and auto-start the application..."

# A) Create systemd override for auto-login on tty1
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
sudo tee /etc/systemd/system/getty@tty1.service.d/override.conf > /dev/null <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin ${CURRENT_USER} --noclear %I \$TERM
EOF

# B) Create ~/.profile to auto-start Xorg on login
# This will only run on the main console (tty1)
tee /home/${CURRENT_USER}/.profile > /dev/null <<'EOF'
# This file is executed on login.
# If on tty1, start the X server.
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
  startx
fi
EOF

# C) Create ~/.xinitrc to launch the main application GUI
# This is what runs inside the Xorg session.
# NOTE: You must edit this to point to your actual GUI renderer script!
tee /home/${CURRENT_USER}/.xinitrc > /dev/null <<'EOF'
#!/bin/bash
cd ~/dasdec

# Set connected display to 720p resolution
DISPLAY_OUT=$(xrandr | grep " connected" | awk '{ print $1 }' | head -n1)
xrandr --output "$DISPLAY_OUT" --mode 1280x720

/home/main/dasdec/venv/bin/python3 /home/main/dasdec/main.py
EOF



echo ""
echo "--- Installation Complete! ---"
echo "The system is now configured."
echo "A reboot is required to apply all changes (especially group memberships and auto-login)."
echo "Please run the 'reboot' command now."