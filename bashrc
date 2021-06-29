alias log="journalctl -e -u greenbich"
alias restart="systemctl stop greenbich && systemctl start greenbich && systemctl status greenbich"
alias status="systemctl status greenbich"
