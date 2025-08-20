from sub_convert import sub_convert
from subs_function import subs_function

import json
import re
import os
import yaml

sub_list_json = './sub/sub_list.json'
sub_merge_path = './sub/'
sub_list_path = './sub/list/'

ipv4 = r"([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})"
ipv6 = r'(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))'
ill = ['|', '?', '[', ']', '@', '!', '%', ':']
valid_ss_cipher_methods = ["aes-128-gcm", "aes-192-gcm", "aes-256-gcm", "aes-128-cfb", "aes-192-cfb", "aes-256-cfb", "aes-128-ctr", "aes-192-ctr", "aes-256-ctr", "rc4-md5", "chacha20-ietf", "xchacha20", "chacha20-ietf-poly1305", "xchacha20-ietf-poly1305"]
valid_ss_plugins = ["obfs","v2ray-plugin"]

class subs:
    def get_subscriptions(content_urls: [], output_path="sub_merge_yaml", should_cleanup=True, specific_files_cleanup=["05.txt"]):
        if not content_urls:
            return

        if should_cleanup:
            for t in os.walk(sub_list_path):
                for f in t[2]:
                    if f not in specific_files_cleanup:
                        f = os.path.join(t[0], f)
                        os.remove(f)
        else:
            for t in os.walk(sub_list_path):
                for f in t[2]:
                    if f in specific_files_cleanup:
                        f = os.path.join(t[0], f)
                        os.remove(f)

        content_list = []
        corresponding_list = []
        corresponding_id = 0
        bad_lines = 0
        for (index, url_container) in enumerate(content_urls):
            ids = url_container['id']
            remarks = url_container['remarks']
            if isinstance(url_container['url'], list):
                for each_url in url_container["url"]:
                    print(f"gather server from {each_url}")
                    content_clash = subs_function.convert_sub(
                        each_url, 'clash', "http://0.0.0.0:25500", False, extra_options="&udp=false")

                    if content_clash in ('Err: No nodes found', 'Err: failed to parse sub'):
                        print("host convertor failed. just continue & ignore...\n")
                    elif content_clash:
                        single_url_gather_quantity = len(list(filter(None, content_clash.split('\n'))))
                        print(f"added content of current url : {single_url_gather_quantity - 1}")

                        clash_content = list(filter(None, content_clash.split('\n')[1:]))

                        if clash_content:
                            safe_clash = []
                            for cl in clash_content:
                                try:
                                    if (re.search(ipv6, str(cl)) is None or re.search(ipv4, str(cl)) is not None) and \
                                       re.search("path: /(.*?)\?(.*?)=(.*?)}", str(cl)) is None:
                                        cl_res = yaml.safe_load(cl)
                                        if cl_res:
                                            try:
                                                cl_temp = yaml.safe_load(str(cl_res[0]))
                                                if cl_temp:
                                                    bad_uuid_format = False
                                                    if 'uuid' in cl_temp and len(cl_temp['uuid']) != 36:
                                                        bad_uuid_format = True
                                                        bad_lines += 1

                                                    if not bad_uuid_format:
                                                        if cl_temp.get('type') in ("ss", "ssr"):
                                                            if cl_temp.get("cipher") in valid_ss_cipher_methods:
                                                                if cl_temp.get('type') == "ss":
                                                                    if 'plugin' in cl_temp:
                                                                        if cl_temp.get('plugin') in valid_ss_plugins:
                                                                            if cl_temp.get('plugin') == 'obfs':
                                                                                if 'plugin-opts' in cl_temp and cl_temp['plugin-opts'].get('mode') in ('http', 'tls'):
                                                                                    safe_clash.append(cl_res)
                                                                                elif 'plugin-opts' not in cl_temp:
                                                                                    safe_clash.append(cl_res)
                                                                                else:
                                                                                    bad_lines += 1
                                                                            elif cl_temp.get('plugin') == 'v2ray-plugin':
                                                                                if 'plugin-opts' in cl_temp and cl_temp['plugin-opts'].get('mode') == 'websocket':
                                                                                    safe_clash.append(cl_res)
                                                                                elif 'plugin-opts' not in cl_temp:
                                                                                    safe_clash.append(cl_res)
                                                                                else:
                                                                                    bad_lines += 1
                                                                            else:
                                                                                safe_clash.append(cl_res)
                                                                        else:
                                                                            bad_lines += 1
                                                                    else:
                                                                        safe_clash.append(cl_res)
                                                                else:
                                                                    safe_clash.append(cl_res)
                                                            else:
                                                                bad_lines += 1
                                                        elif cl_temp.get('type') == "vmess":
                                                            if cl_temp.get("network") in ("h2", "grpc") and cl_temp.get('tls', True) is False:
                                                                bad_lines += 1
                                                            else:
                                                                safe_clash.append(cl_res)
                                                        else:
                                                            safe_clash.append(cl_res)
                                            except Exception:
                                                bad_lines += 1
                                except Exception:
                                    bad_lines += 1

                            if safe_clash:
                                content_list.append("\n".join(clash_content) + "\n")
                                with open(os.path.join(sub_list_path, f'{ids:0>2d}.txt'), 'a+', encoding='utf-8') as f:
                                    f.write("\n".join(clash_content) + "\n")
                                print(f'Writing content of {remarks} to {ids:0>2d}.txt\n')
                                print("Check Points Passed 👍\n")
                                for each_clash_proxy in safe_clash:
                                    corresponding_list.append({"id": corresponding_id, "c_clash": each_clash_proxy})
                                    corresponding_id += 1
                            else:
                                print(f'there is no clash lines {each_url}')
                                print(f'Writing content of {remarks} to {ids:0>2d}.txt\n')
                        else:
                            print(f'there is no clash lines first stage {each_url}')
                            print(f'Writing content of {remarks} to {ids:0>2d}.txt\n')
                    else:
                        print(f'Writing error of {remarks} to {ids:0>2d}.txt\n')

            gather_quantity = len(list(filter(None, ''.join(content_list).split('\n'))))
            print(f"already gathered {gather_quantity}")
            print('\n' + '----------------------------------------------' + '\n')

        print('Merging nodes...\n')
        content_list = list(filter(None, ''.join(content_list).split("\n")))
        print(f"{len(content_list)} lines - {bad_lines} bad lines => total is {len(content_list) - bad_lines}")

        corresponding_list = subs_function.fix_proxies_name(corresponding_proxies=corresponding_list)
        corresponding_list = subs_function.fix_proxies_duplication(corresponding_proxies=corresponding_list)

        print(f"\nfinal sub length => {len(corresponding_list)}")

        clash = [f"  - {x['c_clash']}" for x in corresponding_list]
        content_yaml = 'proxies:\n' + "\n".join(clash)

        with open(os.path.join(sub_merge_path, f'{output_path}.yml'), 'w+', encoding='utf-8') as f:
            f.write(content_yaml)
        print('Done!\n')

if __name__ == "__main__":
    pass
