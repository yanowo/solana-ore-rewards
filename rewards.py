import subprocess
import glob
import datetime
import json

def load_last_execution(file_path):
    try:
        with open(file_path, 'r') as file:
            for last in file:
                pass
            return json.loads(last)
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error reading last execution data: {e}")
        return None

def execute_command(command):
    return subprocess.run(command, capture_output=True, text=True, shell=True)

def print_table_header():
     header = f"{'文件':<5} {'本次獎勵':>12} {'上次獎勵':>12} {'差額':>10}"
     print(header)
     print('-' * 60)

def print_table_row(keypair_name, current_reward, last_reward, diff):
     row = f"{keypair_name:<10} {current_reward:>15.9f} {last_reward:>15.9f} {diff:>15.9f}"
     print(row)

def print_summary(start_time, end_time, total_rewards, diff_rewards, rewards_per_second):
     print()
     print(f"開始時間：{start_time.strftime('%Y-%m-%d %H:%M:%S')}的獎勵總額：{total_rewards:.9f} ORE")
     print(f"結束時間：{end_time.strftime('%Y-%m-%d %H:%M:%S')}的獎勵總額：{total_rewards + diff_rewards:.9f} ORE")
     print()
     print(f"時間間隔：{(end_time - start_time).total_seconds()} 秒")
     print(f"每秒獎勵數：{rewards_per_second:.9f} ORE/s")

def save_keypair_rewards(rewards, file_path):
     with open(file_path, 'w') as file:
         json.dump(rewards, file)

def load_keypair_rewards(file_path):
     try:
         with open(file_path, 'r') as file:
             return json.load(file)
     except FileNotFoundError:
         return {} # 如果沒有找到文件，回傳一個空字典

# 主邏輯開始
ore_exe_path = 'ore.exe'
keypairs_dir = 'keypairs\\*.json'
last_execution_file = 'last_execution.json'
keypair_rewards_file = 'keypair_rewards.json'

last_data = load_last_execution(last_execution_file)
last_keypair_rewards = load_keypair_rewards(keypair_rewards_file)
last_rewards = float(last_data['total_rewards']) if last_data else 0.0
last_time = datetime.datetime.strptime(last_data['time'], '%Y-%m-%d %H:%M:%S') if last_data else datetime.datetime.now()

total_rewards = 0.0
current_time = datetime.datetime.now()

print_table_header()
for keypair_path in glob.glob(keypairs_dir):
    keypair_name = keypair_path.split('\\')[-1]
    command = f'{ore_exe_path} --keypair {keypair_path} rewards'
    process = execute_command(command)
    
    if process.returncode == 0:
        current_reward = float(process.stdout.strip().split()[-2])
        total_rewards += current_reward
        last_reward = last_keypair_rewards.get(keypair_name, 0.0)
        diff = current_reward - last_reward
        last_keypair_rewards[keypair_name] = current_reward
        print_table_row(keypair_name, current_reward, last_reward, diff)
    else:
        print(f"Error executing command for {keypair_path}: {process.stderr}")

save_keypair_rewards(last_keypair_rewards, keypair_rewards_file)

diff_rewards = total_rewards - last_rewards
rewards_per_second = diff_rewards / ((current_time - last_time).total_seconds() if last_time else 1)

print_summary(last_time, current_time, total_rewards, diff_rewards, rewards_per_second)

# Append the current execution data to the log file
with open(last_execution_file, 'a') as file:
    data_to_write = {'time': current_time.strftime('%Y-%m-%d %H:%M:%S'), 'total_rewards': total_rewards}
    file.write(json.dumps(data_to_write) + '\n')
