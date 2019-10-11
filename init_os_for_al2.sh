#!/bin/bash

# Created by Tan.Zhihen
# Func: Set basic config and service on new server
# OS: Amazon Linux 2(Not Amazon Linux)
# Udated: 20190926
# Usage: sh init_os.sh

init_os(){
    # change UTC time to JST time
    timedatectl set-timezone Asia/Tokyo

    # rpcbind:NFSのportmapです。 RPCサービスをそのサービスがリッスンするポートにマッピングする。NFSが使わないので停止します。
    systemctl stop rpcbind.socket
    systemctl stop rpcbind.service
    systemctl disable rpcbind.socket
    systemctl disable rpcbind.service

    # change nofile limit
    cat >> /etc/security/limits.conf << EOF

* soft nofile 65535
* hard nofile 65535
EOF
    
    # change /var/log/messages log level
    sed -i 's/#LogLevel=info/LogLevel=notice/' /etc/systemd/system.conf
    systemctl daemon-reexec

    # change nproc limit
    sed -i 's/4096/65535/' /etc/security/limits.d/20-nproc.conf

    # history setting
    sed -i 's/HISTSIZE=.*/HISTSIZE=99999/' /etc/profile
    sed -i "/HISTSIZE=/a HISTTIMEFORMAT='%Y/%m/%d %H:%M:%S '" /etc/profile

    # prompt setting
    read -p "Please input hostname:" hn
    sed -i '/&& PS1/ s/\\h/\\h('"$hn"')/' /etc/bashrc

    # system parameter
    cat >> /etc/sysctl.conf << EOF

# Optimize system parameter
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_max_syn_backlog = 20480
net.ipv4.tcp_rmem = 4096 873800 1747600
net.ipv4.tcp_wmem = 4096 873800 1747600
net.ipv4.tcp_mem = 2048000 2048000 2048000
net.ipv4.ip_local_port_range = 11000 65500
net.ipv4.tcp_keepalive_time = 10
net.ipv4.tcp_keepalive_probes = 4
net.ipv4.tcp_keepalive_intvl = 5
net.ipv4.tcp_rfc1337 = 1
fs.file-max = 100000
net.core.somaxconn = 65535
EOF

    sysctl -p
}


install_package(){
    # update yum
    yum -y update

    # dstat
    yum -y install dstat
}

pre_check(){
    # If OS version not match, exit
    if ! `grep 'NAME="Amazon Linux 2"' /etc/os-release > /dev/null 2>&1`
        then
        echo "OS version is not Amazon Linux 2"
        exit 1
    fi

    # If OS had been initialized, exit
    if `grep 'HISTSIZE=99999' /etc/profile > /dev/null 2>&1`
        then
        echo "OS had been initialized!"
        exit 0
    fi
}


main(){
    pre_check
    init_os
    install_package
}

main
