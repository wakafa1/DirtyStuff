import os
import sys
import os.path as osp
import sh
import argparse

from common import local_config as lc
from cptdesc import CptBatchDescription
import gem5tasks.typical_o3_config as tc
from common.simulator_task import SimulatorTask, task_wrapper

# `GEM5` Single execution
# Known issue: Ctrl+C will not kill the python script but not GEM5 threads;
# So, when you want to stop batch running
# 1. Ctrl + C to kill the script
# 2. killall -15 gem5.opt or gem5.fast to kill all launched threads

debug = False

# The root dir of GEM5
# gem5_base = '/nfs-nvme/home/zhouyaoyang/projects/xs-gem5'
gem5_base = '/nfs-nvme/home/wangkaifan/xs/gem5/GEM5-internal'
exe = f'{gem5_base}/build/RISCV/gem5.opt'
fs_script = f'{gem5_base}/configs/example/fs.py'

# The directory to store GEM5 outputs (logs, configs, and stats)
top_output_dir = '/nfs-nvme/home/wangkaifan/xs/gem5/gem5-results' # output dir

parser = argparse.ArgumentParser()

parser.add_argument('-t', '--debug-tick', action='store', type=int)
parser.add_argument('-d', '--debug', action='store_true', default=None)
parser.add_argument('-f', '--debug-file', action='store', type=str)
parser.add_argument('-C', '--config', action='store', type=str)
parser.add_argument('-n', '--name', action='store', type=str)
parser.add_argument('-w', '--workload', action='store', type=str)

args = parser.parse_args()

if args.config is not None:
    # You can input the config from command line
    # Example configs are defined in typical_o3_config.py
    CurConf = eval(f'tc.{args.config}')
else:
    CurConf = tc.NanhuNoL3

cwd = os.getcwd()
os.chdir(gem5_base)
tag = sh.git('rev-parse --short HEAD'.split(' ')).strip()

if args.name is not None:
    task_name = args.name
else:
    task_name = "single_run"

if args.workload is not None:
    workload = args.workload
else:
    print("No workload specified, use default workload")
    workload = "/nfs-nvme/home/share/xs-workloads/linux-4.18-hello/bbl.bin"

inst_flags =    ['DynInst']
mem_flags =     ['LSQUnit', 'LSQ', 'MemDepUnit', 'FFLSQ']
dq_flags =      ['DQWake', 'DQ', 'DQPair', 'DQV2', 'DQGOF']
fetch_flags =   ['Branch', 'Fetch', 'LoopBuffer']
exec_flags =    ['FUW', 'ObExec']
check_flags =   ['ValueCommit']
nosq_flags =    ['NoSQSMB', 'NoSQPred']
omega_flags =   ['FFCPU', 'DAllocation', 'FFSquash', 'DIEWC', 'FFExec', 'Commit', 'FFCommit',
        'FFInit', 'Rename', 'IEW', 'FFDisp']
fault_flags = ['RiscvMisc', 'Fault', 'PageTableWalker', 'TLB']

backend_flags = omega_flags + check_flags + mem_flags + nosq_flags + dq_flags + exec_flags + \
        inst_flags + fault_flags
frontend_flags = fetch_flags + fault_flags + inst_flags

debug_tick = None
debug_flags = []
debug_file = None
if args.debug:
    debug_flags = ['CacheAll', 'RiscvMisc']

if args.debug_file:
    debug_file = args.debug_file

if args.debug_tick is not None:
    debug_tick = args.debug_tick
    debug_flags = frontend_flags + backend_flags

task = CurConf(
    exe,
    top_output_dir,
    task_name,
    task_name,
    0
)

task.sub_workload_level_path_format()
task.set_trivial_workdir()
task.avoid_repeat = False

if len(debug_flags):
    df_str = '--debug-flags=' + ','.join(debug_flags)
    task.add_direct_options([df_str])

if debug_file is not None:
    df_str = '--debug-file=' + debug_file
    task.add_direct_options([df_str])

if debug_tick is not None:
    start = max(0, debug_tick - 40000 * 500)
    end =          debug_tick + 10000 * 500
    task.add_direct_options([
        f'--debug-start={start}',
        f'--debug-end={end}',
        ])

task.add_direct_options([fs_script]) # direct_options are passed to gem5.opt

# dict_options are passed to fs.py
task.add_dict_options({
    # This option provides us a method to override the "GCPT restorer" when loading
    # the RISC-V generic checkpoint.
    # resource/gcpt_restore can be found in https://github.com/OpenXiangShan/NEMU/tree/cpp-gem5
    '--gcpt-restorer': '/nfs-nvme/home/wangkaifan/xs/gem5/NEMU/resource/gcpt_restore/build/gcpt.bin',

    '--generic-rv-cpt': workload,
    '--dramsim3-ini': '/nfs-nvme/home/wangkaifan/xs/gem5/GEM5-internal/xiangshan_DDR4_8Gb_x8_2400.ini',
})

if not workload[-3:] == ".gz":
    task.add_direct_options([
        '--raw-cpt'
    ])

task.format_options()
task.set_output2file(False)

task_wrapper(task)
print(f'Finished simulation')
