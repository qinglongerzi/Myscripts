#!/bin/bash

# Created by Tan.Zhihen
# Func: Set basic config and service on new server
# OS: Amazon Linux AMI(Not Amazon Linux 2 AMI)
# Udated: 20190417
# Usage: sh init_os.sh

init_os(){
    # change UTC time to JST time
    sed -i 's/ZONE="UTC"/ZONE="Japan"/' /etc/sysconfig/clock
    ln -sf /usr/share/zoneinfo/Japan /etc/localtime

    # stop service unneccessary
    # acpid:省電力用休止状態をサポート。本来ノートPC用で通常のサーバーでは不要です。
    # chkconfig acpid off
    # service acpid stop

    # atd:単発的にスケジュール化した コマンド を実行させるデーモン。セキュリティとトラブルシューティングのため停止します。
    # chkconfig atd off
    # service atd stop

    # auditd:SELinuxの詳細なログを収集する。SELinuxを使わないので不要です。
    # chkconfig auditd off
    # service auditd stop

    # ip6tables:ファイアウォールの役目はAWSセキュリティグループに任せるので不要です。
    chkconfig ip6tables off
    service ip6tables stop

    # iptables:ファイアウォールの役目はAWSセキュリティグループに任せるので不要です。
    chkconfig iptables off
    service iptables stop

    # mdmonitor:ソフトウェアRAID管理デーモン。ソフトウェアRAIDが使わないので停止します。
    # chkconfig mdmonitor off
    # service mdmonitor stop

    # netfs:Network File System(NFS) クライアントデーモン。NFSが使わないので停止します。
    chkconfig netfs off
    service netfs stop

    # nfslock:NFSのファイル・ロック機能を提供するサービス。NFSが使わないので停止します。
    chkconfig nfslock off
    service nfslock stop

    # rpcbind:NFSのportmapです。 RPCサービスをそのサービスがリッスンするポートにマッピングする。NFSが使わないので停止します。
    chkconfig rpcbind off
    service rpcbind stop

    # rpcgssd:NFSのRPCにおいてセキュリティコンテキストを生成するデーモンです。NFSが使わないので停止します。
    chkconfig rpcgssd off
    service rpcgssd stop

    # sendmail:送信サービス。不要です。
    # chkconfig sendmail off
    # service sendmail stop

    # change nofile limit
    cat >> /etc/security/limits.conf << EOF

* soft nofile 65535
* hard nofile 65535
EOF
    
    # change nproc limit
    cat >> /etc/security/limits.d/90-nproc.conf << EOF
*          soft    nproc     65535
root       soft    nproc     unlimited
EOF

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

    # install packages
    yum -y install dstat \
                   git

    # nscd:  A Name Service Caching Daemon
    yum -y install nscd
    nscd_config=/etc/nscd.conf
    # debug-level 1
    sed -i 's/\(debug-level[^ <]\+\?\)0/\11/' ${nscd_config}
    # paranoia yes
    sed -i 's/\(paranoia[^ <]\+\?\)no/\1yes/' ${nscd_config}
    # restart-interval 60
    sed -i 's/#\(.\+\?restart-interval[^ <]\+\?\)3600/\160/' ${nscd_config}
    # enable-cache            passwd          no
    sed -i 's/\(enable-cache.\+\?passwd.\+\?\)yes/\1no/' ${nscd_config}
    # enable-cache            group          no
    sed -i 's/\(enable-cache.\+\?group.\+\?\)yes/\1no/' ${nscd_config}
    # enable-cache            services          no
    sed -i 's/\(enable-cache.\+\?services.\+\?\)yes/\1no/' ${nscd_config}
    # enable-cache            netgroup          no
    sed -i 's/\(enable-cache.\+\?netgroup.\+\?\)yes/\1no/' ${nscd_config}
    # positive-time-to-live   hosts           60
    sed -i '/hosts/ s/\(positive-time-to-live.\+\?hosts.\+\?\)3600/\160/' ${nscd_config}
    # persistent              hosts           no
    sed -i '/hosts/ s/\(persistent.\+\?hosts.\+\?\)yes/\1no/' ${nscd_config}

    chkconfig nscd on
    service nscd start

    # Change ntpd to chronyd for preventing the query blocked by aws security group. The default time server of chronyd is AWS time server.
    service ntpd stop
    yum -y remove ntp*
    yum -y install chrony
    chkconfig chronyd on
    service chronyd start
    chronyc sources -v
}

pre_check(){
    # If OS version not match, exit
    if ! `grep 'NAME="Amazon Linux AMI"' /etc/os-release > /dev/null 2>&1`
        then
        echo "OS version is not Amazon Linux AMI"
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
