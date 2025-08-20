#!/usr/bin/env python3

import json
import re
import os
import yaml
import argparse
import time
from urllib import request

from sub_convert import sub_convert
from list_update import update_url
from get_subs import subs
from subs_function import subs_function


# 文件路径定义
readme = './README.md'
sub_merge_path = './sub/'
sub_list_path = './sub/list/'
provider_path = './update/provider/'
update_path = './update/'
config_file = './update/provider/config.yml'

class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

def substrings(string, left, right):
    value = string.replace('\n', '').replace(' ', '')
    start = value.find(left)
    if start == -1:
        return ''
    start += len(left)
    end = value.find(right, start)
    if end == -1:
        return ''
    return value[start:end]

def read_list(json_file, remote=False):
    with open(json_file, 'r', encoding='utf-8') as f:
        raw_list = json.load(f)
    input_list = []
    for item in raw_list:
        if item.get('enabled', False):
            urls = re.split(r'\|', item['url']) if not remote else item['url']
            item['url'] = urls
            input_list.append(item)
    return input_list

def geoip_update(url):
    print('Downloading Country.mmdb...')
    try:
        request.urlretrieve(url, './utils/Country.mmdb')
        print('Success!\n')
    except Exception as e:
        print(f'Failed! {e}\n')

def readme_update(readme_file='./README.md', sub_list=[]):
    print('Update README.md file...')
    with open(readme_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    with open('./sub/sub_merge.txt', 'r', encoding='utf-8') as f:
        total = len(f.readlines())

    thanks = []
    for repo in sub_list:
        if repo.get('enabled', False):
            try:
                sub_file = f'./sub/list/{repo["id"]:0>2d}.txt'
                with open(sub_file, 'r', encoding='utf-8') as f:
                    proxies = f.readlines()
                    amount = 0 if proxies in (['Url 解析错误'], ['订阅内容解析错误']) else len(proxies)
                line = f'- [{repo["remarks"]}]({repo["site"]}), number of nodes: `{amount}`\n'
                thanks.append(line)
            except (FileNotFoundError, KeyError) as e:
                print(f"Skipping repo due to error: {e}")

    # Update high-speed node count
    for i, line in enumerate(lines):
        if '### high-speed node' in line:
            with open('./Eternity', 'r', encoding='utf-8') as f:
                proxies_base64 = f.read()
                proxies = sub_convert.base64_decode(proxies_base64).split('\n')
                proxies = [f'    {p}\n' for p in proxies if p]
            top_amount = len(proxies)
            lines[i + 2] = f'high-speed node quantity: `{top_amount}`\n'
            # Clear old proxies
            del lines[i+4:]
            for proxy in proxies:
                lines.append(proxy)
            break

    # Update all nodes count
    for i, line in enumerate(lines):
        if '### all nodes' in line:
            with open('./sub/sub_merge_yaml.yml', 'r', encoding='utf-8') as f:
                top_amount = len(f.readlines()) - 1
            lines[i + 1] = f'merge nodes w/o dup: `{top_amount}`\n'
            break

    # Update node sources
    for i, line in enumerate(lines):
        if '### node sources' in line:
            # Clear old sources
            del lines[i+1:]
            for thank in thanks:
                lines.append(thank)
            break

    with open(readme_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print('Finish!\n')

def convert_and_save(sub_type):
    if sub_type == 'public':
        eterniy_file = './Eternity'
        eternity_yml_file = './Eternity.yml'
        log_file = './LogInfo.txt'
        base64_url = "https://raw.githubusercontent.com/mahdibland/SSAggregator/master/sub/sub_merge_base64.txt"
        provider_file = provider_path + 'provider-all.yml'
    elif sub_type == 'airport':
        eterniy_file = './EternityAir'
        eternity_yml_file = './EternityAir.yml'
        log_file = './LogInfoAir.txt'
        base64_url = "https://raw.githubusercontent.com/mahdibland/SSAggregator/master/sub/airport_merge_base64.txt"
        provider_file = provider_path + 'provider-all-airport.yml'
    else:
        return

    all_provider = subs_function.convert_sub(base64_url, 'clash', "http://0.0.0.0:25500", False, extra_options="&udp=false")

    with open(log_file, 'r') as f:
        log_lines = f.readlines()

    temp_providers = all_provider.split('\n')
    for i, line in enumerate(temp_providers):
        if line != 'proxies:':
            try:
                server_name = substrings(line, "name:", ",")
                server_type = substrings(line, "type:", ",")
                log_lines[i] = f"name: {server_name} | type: {server_type} | {log_lines[i]}"
            except IndexError:
                print("log lines length != providers length")

    with open(log_file, 'w') as f:
        f.writelines(log_lines)

    removed_bad_char = [line for line in all_provider.split("\n")[1:] if "�" not in line]
    log_lines_without_bad_char = [line for line in log_lines if "�" not in line]

    num = 200
    num = min(len(removed_bad_char), num)

    if sub_type == 'airport':
        removed_bad_char = [item for i, item in enumerate(removed_bad_char[:num + 1]) if "avg_speed: 0.0 MB" not in log_lines_without_bad_char[i]]

    all_provider = "proxies:\n" + "\n".join(removed_bad_char)

    proxy_all = []
    skip_names_index = []
    for i, line in enumerate(re.split(r'\n+', all_provider)):
        if line != 'proxies:':
            try:
                name = substrings(line, "name:", ",")
                speed = substrings(log_lines_without_bad_char[i], "avg_speed:", "|")
                line = re.sub("name:( |)(.*?),", f"name: {name} | {speed},", line)
            except IndexError:
                pass

            line = line.replace('- ', '')
            line_parsed = yaml.safe_load(line)

            if "password" in line_parsed:
                password = str(line_parsed.get("password"))
                line_parsed["password"] = password
                if re.match(r'^\d+\.?\d*[eE][-+]?\d+$', password):
                    skip_names_index.append(i)
                    continue

            proxy_all.append(line_parsed)

    with open(provider_file, 'w', encoding='utf-8') as f:
        f.write(all_provider)

    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f.read())

    provider_dic = {'proxies': yaml.safe_load(all_provider)['proxies']}

    all_name = []
    for i, proxy in enumerate(provider_dic.get('proxies', [])):
        if i not in skip_names_index:
            try:
                speed = substrings(log_lines_without_bad_char[i], "avg_speed:", "|")
                all_name.append(f"{proxy['name'].replace(' ', '')} | {speed}")
            except (IndexError, KeyError):
                all_name.append(proxy['name'].replace(' ', ''))

    if not provider_dic.get('proxies'):
        all_name.append('DIRECT')

    proxy_groups = config.get('proxy-groups', [])
    proxy_group_fill = [rule['name'] for rule in proxy_groups if rule.get('proxies') is None]

    full_size = len(all_name)
    part_size = full_size // 4
    for rule in proxy_groups:
        if rule['name'] in proxy_group_fill:
            if "Tier 1" in rule['name']:
                rule['proxies'] = all_name[:part_size]
            elif "Tier 2" in rule['name']:
                rule['proxies'] = all_name[part_size:part_size*2]
            elif "Tier 3" in rule['name']:
                rule['proxies'] = all_name[part_size*2:part_size*3]
            elif "Tier 4" in rule['name']:
                rule['proxies'] = all_name[part_size*3:]

    config['proxies'] = proxy_all
    config['proxy-groups'] = proxy_groups

    with open(eternity_yml_file, 'w+', encoding='utf-8') as f:
        f.write(yaml.dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True, width=750, indent=2, Dumper=NoAliasDumper))

    if sub_type == 'public':
        try:
            date = time.strftime('%y%m', time.localtime())
            date_day = time.strftime('%y%m%d', time.localtime())
            os.makedirs(f'{update_path}{date}', exist_ok=True)
            with open(eterniy_file, 'r', encoding='utf-8') as f:
                sub_content = f.read()
            with open(os.path.join(update_path, date, f'{date_day}.txt'), 'w', encoding='utf-8') as f:
                f.write(sub_convert.base64_decode(sub_content))
        except Exception as e:
            print(f"Error while backing up {eterniy_file}: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--type', type=str, default='public', help='Type of subscription to process (public or airport)')
    args = parser.parse_args()

    if args.type == 'public':
        sub_list_json = './sub/sub_list.json'
        update_url.update_main(use_airport=False, airports_id=[5], sub_list_json=sub_list_json)
        geoip_update('https://raw.githubusercontent.com/Loyalsoldier/geoip/release/Country.mmdb')
        sub_list = read_list(sub_list_json)
        subs.get_subscriptions(list(filter(lambda x: x['id'] != 5, sub_list)))
        readme_update(readme, sub_list)
        convert_and_save('public')
    elif args.type == 'airport':
        sub_list_airport_json = './sub/sub_list_airport.json'
        update_url.update_main(use_airport=True, airports_id=[5], sub_list_json=sub_list_airport_json)
        sub_list = read_list(sub_list_airport_json)
        subs.get_subscriptions(
            list(filter(lambda x: x['id'] == 5, sub_list)),
            output_path="airport_merge_yaml",
            should_cleanup=False,
            specific_files_cleanup=["05.txt"]
        )
        convert_and_save('airport')

if __name__ == '__main__':
    main()
