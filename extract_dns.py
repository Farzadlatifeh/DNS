#!/usr/bin/env python3
"""
Extract DNS IP addresses from the gist and save them in a JSON file.
Separates IPv4, DNS64, and IPv6 addresses.
Each profile has at most one primary and one secondary IP.
"""

import json
import re
from urllib.request import urlopen


def fetch_gist_content():
    """Fetch the raw content from the GitHub Gist."""
    url = "https://gist.githubusercontent.com/mutin-sa/5dcbd35ee436eb629db7872581093bc5/raw/"
    with urlopen(url) as response:
        return response.read().decode('utf-8')


def parse_dns_table(content):
    """Parse the main DNS table and extract IPs by organization."""
    org_data = {}
    
    # Find the DNS section (not DNS64)
    dns_start = content.find('# DNS:')
    if dns_start == -1:
        return org_data
    
    # Find the next section (# DNS64:)
    dns64_start = content.find('# DNS64:', dns_start)
    if dns64_start == -1:
        dns64_start = len(content)
    
    section_content = content[dns_start:dns64_start]
    
    # Parse table rows using simpler pattern
    lines = section_content.split('\n')
    for line in lines:
        if not line.strip().startswith('|'):
            continue
        
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 8:
            continue
        
        ipv4 = parts[1] if len(parts) > 1 else ''
        ipv6 = parts[2] if len(parts) > 2 else ''
        org = parts[7] if len(parts) > 7 else ''
        
        # Skip header rows and separator rows
        if 'IPv4' in ipv4 or ipv4.startswith('-') or ':' in ipv4 or ipv4 == '':
            continue
        
        if not org or org.startswith('-') or 'Org' in org:
            continue
            
        if org not in org_data:
            org_data[org] = {'ipv4': [], 'ipv6': []}
        
        if ipv4 and re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ipv4):
            org_data[org]['ipv4'].append(ipv4)
        if ipv6 and ':' in ipv6 and not ipv6.startswith('-'):
            org_data[org]['ipv6'].append(ipv6)
    
    return org_data


def parse_dns64_table(content):
    """Parse the DNS64 table and extract IPs by organization."""
    org_data = {}
    
    # Find the DNS64 section
    dns64_start = content.find('# DNS64:')
    if dns64_start == -1:
        return org_data
    
    # Find the next section (## Google)
    next_section = re.search(r'\n## ', content[dns64_start + 10:])
    if next_section:
        section_end = dns64_start + 10 + next_section.start()
    else:
        section_end = len(content)
    
    section_content = content[dns64_start:section_end]
    
    # Parse table rows
    lines = section_content.split('\n')
    for line in lines:
        if not line.strip().startswith('|'):
            continue
        
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 7:
            continue
        
        ipv6 = parts[1] if len(parts) > 1 else ''
        org = parts[6] if len(parts) > 6 else ''
        
        # Skip header rows and separator rows
        if 'IPv6' in ipv6 or ipv6.startswith('-') or org.startswith('-') or 'Org' in org:
            continue
        
        # Validate IPv6 format (must have proper format, not just colons)
        if not org or ':' not in ipv6 or len(ipv6) < 4:
            continue
        
        # Additional validation for IPv6 addresses (allow :: compression)
        if not re.match(r'^[0-9a-fA-F:]+$', ipv6):
            continue
        # Ensure it's a valid IPv6 pattern (at least has proper structure)
        if not re.match(r'^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$', ipv6):
            continue
            
        if org not in org_data:
            org_data[org] = {'ipv6': []}
        
        if ipv6 and ':' in ipv6:
            org_data[org]['ipv6'].append(ipv6)
    
    return org_data


def extract_all_dns_data(content):
    """Extract all DNS data from the content."""
    result = {
        'ipv4_profiles': [],
        'ipv6_profiles': [],
        'dns64_profiles': []
    }
    
    # Track processed organizations to avoid duplicates
    processed_orgs = set()
    
    # Parse main DNS table
    dns_table_data = parse_dns_table(content)
    
    profile_num = 1
    for org, data in dns_table_data.items():
        processed_orgs.add(org.lower())
        
        # Remove duplicates while preserving order
        ipv4_unique = list(dict.fromkeys(data['ipv4']))
        ipv6_unique = list(dict.fromkeys(data['ipv6']))
        
        # Create profiles for IPv4 (max 2 IPs)
        if ipv4_unique:
            profile = {
                'profile_number': profile_num,
                'profile_name': org[:50],
                'primary': ipv4_unique[0] if len(ipv4_unique) >= 1 else None,
                'secondary': ipv4_unique[1] if len(ipv4_unique) >= 2 else None
            }
            result['ipv4_profiles'].append(profile)
            profile_num += 1
        
        # Create profiles for IPv6 from the same org (max 2 IPs)
        if ipv6_unique:
            profile = {
                'profile_number': profile_num,
                'profile_name': org[:50],
                'primary': ipv6_unique[0] if len(ipv6_unique) >= 1 else None,
                'secondary': ipv6_unique[1] if len(ipv6_unique) >= 2 else None
            }
            result['ipv6_profiles'].append(profile)
            profile_num += 1
    
    # Parse DNS64 table
    dns64_table_data = parse_dns64_table(content)
    
    # Track which orgs have been processed from the DNS64 table
    dns64_orgs_processed = set()
    
    for org, data in dns64_table_data.items():
        ipv6_unique = list(dict.fromkeys(data['ipv6']))
        
        if ipv6_unique:
            profile = {
                'profile_number': profile_num,
                'profile_name': f"{org} DNS64"[:50],
                'primary': ipv6_unique[0] if len(ipv6_unique) >= 1 else None,
                'secondary': ipv6_unique[1] if len(ipv6_unique) >= 2 else None
            }
            result['dns64_profiles'].append(profile)
            profile_num += 1
            dns64_orgs_processed.add(org.lower())
    
    # Parse detailed sections for additional organizations not in tables
    detailed_sections = re.findall(r'## (.*?) \[AS\d+\]:([\s\S]*?)(?=## |\Z)', content)
    
    for section_title, section_content in detailed_sections:
        # Extract org name from title
        org_name = section_title.split(' [')[0].strip()
        
        # Skip if already processed (case-insensitive comparison)
        if org_name.lower() in processed_orgs:
            continue
        
        # Skip DNS64 extraction if org already processed from DNS64 table
        skip_dns64 = org_name.lower() in dns64_orgs_processed
        
        # Extract IPv4 addresses from pairs (IPv4/IPv6 format)
        ipv4_addrs = re.findall(r'(\d{1,3}(?:\.\d{1,3}){3})/', section_content)
        
        # Extract standalone IPv4 addresses (lines with only an IP)
        standalone_ipv4 = re.findall(r'^(\d{1,3}(?:\.\d{1,3}){3})$', section_content, re.MULTILINE)
        ipv4_addrs.extend(standalone_ipv4)
        
        # Extract IPv6 addresses from pairs
        ipv6_addrs = re.findall(r'/([0-9a-fA-F:]+(?:\.[0-9a-fA-F:]+)*)', section_content)
        
        # Extract DNS64 addresses
        dns64_ips = []
        dns64_match = re.search(r'DNS64:\s*\n([\s\S]*?)(?=\n##|\n\n[A-Z]|\Z)', section_content)
        if dns64_match:
            dns64_section = dns64_match.group(1)
            # Match full IPv6 addresses (including :: compression) followed by space or parenthesis
            dns64_ips = re.findall(r'([0-9a-fA-F]+(?::[0-9a-fA-F]*){2,}::[0-9a-fA-F]*)', dns64_section)
        
        # Deduplicate and limit to 2
        ipv4_unique = list(dict.fromkeys(ipv4_addrs))[:2]
        ipv6_unique = list(dict.fromkeys(ipv6_addrs))[:2]
        dns64_unique = list(dict.fromkeys(dns64_ips))[:2]
        
        if ipv4_unique:
            profile = {
                'profile_number': profile_num,
                'profile_name': org_name[:50],
                'primary': ipv4_unique[0] if len(ipv4_unique) >= 1 else None,
                'secondary': ipv4_unique[1] if len(ipv4_unique) >= 2 else None
            }
            result['ipv4_profiles'].append(profile)
            profile_num += 1
        
        if ipv6_unique:
            profile = {
                'profile_number': profile_num,
                'profile_name': org_name[:50],
                'primary': ipv6_unique[0] if len(ipv6_unique) >= 1 else None,
                'secondary': ipv6_unique[1] if len(ipv6_unique) >= 2 else None
            }
            result['ipv6_profiles'].append(profile)
            profile_num += 1
        
        if dns64_unique and not skip_dns64:
            profile = {
                'profile_number': profile_num,
                'profile_name': f"{org_name} DNS64"[:50],
                'primary': dns64_unique[0] if len(dns64_unique) >= 1 else None,
                'secondary': dns64_unique[1] if len(dns64_unique) >= 2 else None
            }
            result['dns64_profiles'].append(profile)
            profile_num += 1
    
    return result


def main():
    """Main function to extract DNS data and save to JSON."""
    print("Fetching DNS data from GitHub Gist...")
    content = fetch_gist_content()
    
    print("Extracting DNS information...")
    dns_data = extract_all_dns_data(content)
    
    # Re-number profiles sequentially within each category
    for key in ['ipv4_profiles', 'ipv6_profiles', 'dns64_profiles']:
        for i, profile in enumerate(dns_data[key], 1):
            profile['profile_number'] = i
    
    # Deduplicate profiles by IP addresses and shorten names
    dns_data = deduplicate_and_shorten_names(dns_data)
    
    # Re-number again after deduplication
    for key in ['ipv4_profiles', 'ipv6_profiles', 'dns64_profiles']:
        for i, profile in enumerate(dns_data[key], 1):
            profile['profile_number'] = i
    
    # Save to JSON file
    output_file = 'dns_profiles.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dns_data, f, indent=2, ensure_ascii=False)
    
    print(f"DNS profiles saved to {output_file}")
    print(f"Total IPv4 profiles: {len(dns_data['ipv4_profiles'])}")
    print(f"Total IPv6 profiles: {len(dns_data['ipv6_profiles'])}")
    print(f"Total DNS64 profiles: {len(dns_data['dns64_profiles'])}")


def shorten_name(name, is_dns64=False):
    """Shorten profile names to be concise."""
    # Remove common verbose patterns
    name = name.replace(' Public DNS', '')
    name = name.replace(' DNS', '')
    name = name.replace('-', '')
    name = name.replace('/', '')
    name = name.replace(' ', '')
    
    # Add DNS64 suffix if needed
    if is_dns64 and not name.endswith('64'):
        name = name + '64'
    
    return name[:50]


def deduplicate_and_shorten_names(dns_data):
    """Remove duplicate profiles with same IPs and shorten names."""
    result = {
        'ipv4_profiles': [],
        'ipv6_profiles': [],
        'dns64_profiles': []
    }
    
    for category in ['ipv4_profiles', 'ipv6_profiles', 'dns64_profiles']:
        seen_ips = set()
        is_dns64 = category == 'dns64_profiles'
        
        for profile in dns_data[category]:
            # Create a key from the IP addresses
            ip_key = (profile.get('primary'), profile.get('secondary'))
            
            # Skip if we've already seen this IP combination
            if ip_key in seen_ips:
                continue
            
            seen_ips.add(ip_key)
            
            # Shorten the profile name
            profile['profile_name'] = shorten_name(profile['profile_name'], is_dns64)
            
            result[category].append(profile)
    
    return result


if __name__ == '__main__':
    main()
