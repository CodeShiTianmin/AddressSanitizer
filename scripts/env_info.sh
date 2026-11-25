#!/usr/bin/env bash
# Print the environment that affects the results (recorded in results/env.txt).
echo "date:        $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "kernel:      $(uname -srvm)"
echo "os:          $(. /etc/os-release; echo "$PRETTY_NAME") (container)"
echo "cpu:         $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | xargs)"
echo "cpu_model:   family $(grep -m1 'cpu family' /proc/cpuinfo | cut -d: -f2 | xargs) model $(grep -m1 '^model' /proc/cpuinfo | cut -d: -f2 | xargs)"
echo "nproc:       $(nproc)"
echo "hypervisor:  $(grep -q hypervisor /proc/cpuinfo && echo yes || echo no)"
echo "mem_total:   $(grep MemTotal /proc/meminfo | awk '{print $2" kB"}')"
echo "aslr:        $(cat /proc/sys/kernel/randomize_va_space)"
echo "thp:         $(cat /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null)"
echo "governor:    $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo 'n/a (VM)')"
echo "clang:       $(clang --version | head -1)"
echo "glibc:       $(ldd --version | head -1)"
echo "python:      $(python3 --version)"
echo "cache:"; lscpu | grep -i cache | sed 's/^/  /'
