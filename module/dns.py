import requests
import json
import dns.resolver
from dotenv import load_dotenv
import os
import ipinfo
import socket

import pprint

def fetch_networkcalc(domain):
   print('[-] Fetching networkcalc')
   IPs_v4 = []
   mail_servers = []

   try:
      url = f'https://networkcalc.com/api/dns/lookup/{domain}'
      response = requests.get(url)
      data = response.json()

      if data['status'] == 'NO_RECORDS':
         return IPs_v4, mail_servers
      else:
         for record_A in data['records']['A']:
            IPs_v4.append(record_A['address'])

         for record_MX in data['records']['MX']:
            mail_servers.append(f"{record_MX['priority']} {record_MX['exchange']}")

      return IPs_v4, mail_servers
   except (requests.RequestException, json.JSONDecodeError):
      return IPs_v4, mail_servers
   
def fetch_hackertarget(domain):
   print('[-] Fetching Hacker Target')
   IPs_v4 = []
   IPs_v6 = []
   mail_servers = []

   try:
      url = f'https://api.hackertarget.com/dnslookup/?q={domain}&output=json'
      response = requests.get(url)
      data = response.json()
      
      if 'error' in data:
         return IPs_v4, IPs_v6, mail_servers
      else:
         for record_A in data['A']:
            IPs_v4.append(record_A)

         for record_AAAA in data['AAAA']:
            IPs_v6.append(record_AAAA)

         for record_MX in data['MX']:
            mail_servers.append(record_MX)

      return IPs_v4, IPs_v6, mail_servers
   except (requests.RequestException, json.JSONDecodeError):
      return IPs_v4, IPs_v6, mail_servers

def dns_ip_query(domain, record_type, isp):
   resolver = dns.resolver.Resolver()
   resolver.nameservers = [isp]

   IPs = [] 
   try:
      response = resolver.resolve(domain,record_type)
      for data in response:
         IPs.append(str(data))
      return IPs
   except Exception:
      return IPs

def dns_mail_server_query(domain, record_type, isp):
   resolver = dns.resolver.Resolver()
   resolver.nameservers = [isp]
   
   mail_servers = []
   try:
      response = resolver.resolve(domain,record_type)
      for data in response:
         mail_servers.append(f"{data.preference} {data.exchange}")
      return mail_servers
   except Exception:
      return mail_servers

def fetch_public_isp(domain,isp):
   return dns_ip_query(domain,'A',isp), dns_ip_query(domain,'AAAA',isp), dns_mail_server_query(domain,'MX',isp)

import asyncio

def fetch_ipinfo_localtion(ip,is_trail,api_key):
   
   if not api_key:
      return 'IPinfo key missing'
   
   handler = ipinfo.getHandler(api_key)
   async def do_req():
      details = handler.getDetails(ip)
      if is_trail:
         return f'{details.all["ip"]} Contact: {details.all["abuse"]["email"]}#{details.all["abuse"]["name"]}#{details.all["abuse"]["phone"]} Org: {details.all["company"]["name"]}# Region:{details.all["company"]["domain"]} {details.all["region"]}'
      else:
         return f'{details.all["ip"]} Host: {details.all["hostname"]} Org: {details.all["org"]} Region: {details.all["region"]}'
      
   loop = asyncio.get_event_loop()
   result = loop.run_until_complete(do_req())
   return result

def fetching_reverse_dns_from_ipv4(ip,api_key):
   try:
      url = f'https://ipinfo.io/domains/{ip}?token={api_key}'
      response = requests.get(url)
      data = response.json()

      return data['domains']

   except (requests.RequestException, json.JSONDecodeError):
      return []

def redict_fetching_reverse_dns_from_ipv4(ip):
   try:
        host_name = socket.gethostbyaddr(ip)
        return host_name
   except socket.herror:
        return []
   
def ip_dns_lookup(domain,is_trail,folder_sample):
   ip_dns_report = folder_sample + '/' + folder_sample + '@ip_dns.txt'
   networkcalc_ip_v4, networkcalc_mail_servers = fetch_networkcalc(domain)
   hackertarget_ip_v4, hackertarget_ip_v6, hackertarget_mail_servers = fetch_hackertarget(domain)
   print('[-] Fetching Google ISP')
   gg_ip_v4, gg_ip_v6, gg_mail_servers = fetch_public_isp(domain,'8.8.8.8')
   print('[-] Fetching Cloudflare ISP')
   cloudflare_ip_v4_1, cloudflare_ip_v6_1, cloudflare_mail_servers_1 = fetch_public_isp(domain,'1.1.1.1')
   cloudflare_ip_v4_2, cloudflare_ip_v6_2, cloudflare_mail_servers_2 = fetch_public_isp(domain,'1.0.0.1')
   
   ip_v4_set = list(set(networkcalc_ip_v4 + hackertarget_ip_v4 + gg_ip_v4 + cloudflare_ip_v4_1 + cloudflare_ip_v4_2))
   ip_v6_set = list(set(hackertarget_ip_v6 + gg_ip_v6 + cloudflare_ip_v6_1 + cloudflare_ip_v6_2))
   mail_servers_set = list(set(networkcalc_mail_servers + hackertarget_mail_servers + gg_mail_servers + cloudflare_mail_servers_1 + cloudflare_mail_servers_2))

   with open(ip_dns_report, 'w') as file:
      file.write('IP V4 set:\n')
      for ip_v4 in ip_v4_set:
         file.write(f'{ip_v4}\n')
      file.write('\n')

      file.write('IP V6 set:\n')
      for ip_v6 in ip_v6_set:
         file.write(f'{ip_v6}\n')
      file.write('\n')

      file.write('Mail Server set:\n')
      for mx in mail_servers_set:
         file.write(f'{mx}\n')
      file.write('\n')

   load_dotenv()
   api_key = os.getenv('IPinfo_API_KEY')

   print('[+] Reverse DNS')
   if api_key:
      print('[-] Fetching IPinfo')
      reverse_dns_set = []
      for ip in ip_v4_set:
         reverse_dns_set = reverse_dns_set + fetching_reverse_dns_from_ipv4(ip,api_key) + [redict_fetching_reverse_dns_from_ipv4(ip)[0]]
      filter_reverse_dns_set = list(set(reverse_dns_set))
      with open(ip_dns_report, 'a') as file:
         file.write('Reverse DNS:\n')
         for reverse_dns in filter_reverse_dns_set:
            file.write(f'{reverse_dns}\n')
         file.write('\n')

   print('[+] Localtion, Hosting Provider, Region')
   if api_key:
      print('[-] Fetching IPinfo')
      with open(ip_dns_report, 'a') as file:
         file.write('Localtion, Hosting Provider, Region:\n')
         for ip in ip_v4_set:
            text = fetch_ipinfo_localtion(ip,is_trail,api_key)
            file.write(f'{text}\n')
         file.write('\n')
         
      