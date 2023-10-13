import sys
import boto3
import botocore
from colorama import Fore, Style, init
import argparse
import concurrent.futures

# Initialize colorama
init(autoreset=True)

# Initialize the S3 client without providing credentials
s3_client = boto3.client('s3')

# List of all AWS regions
regions = boto3.session.Session().get_available_regions('s3')

# Read bucket names from a file
with open('bucket_names.txt', 'r') as file:
    bucket_names = [line.strip() for line in file.readlines()]

# Function to check if a bucket exists in a given region
def check_bucket_existence(bucket_name, region):
    try:
        s3_client = boto3.client('s3', region_name=region)
        s3_client.head_bucket(Bucket=bucket_name)
        try:
            s3_client.list_objects(Bucket=bucket_name)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "AccessDenied":
                return "Exists but Access Denied"
            elif e.response['Error']['Code'] == "Forbidden":
                return "Exists but Forbidden"
            else:
                raise
        return "Exists"
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            return False
        elif e.response['Error']['Code'] == "403":
            return "Exists but Forbidden"
        else:
            raise

def check_buckets_in_region(keyword, output_accessible, output_access_denied, output_forbidden):
    success_color = Fore.GREEN
    error_color = Fore.RED
    warning_color = Fore.YELLOW

    for region in regions:
        for bucket_name in bucket_names:
            full_bucket_name = bucket_name.replace('%s', keyword)
            result = check_bucket_existence(full_bucket_name, region)
            if result == "Exists":
                print(success_color + f'Bucket {full_bucket_name} exists in {region}')
                if output_accessible:
                    with open(output_accessible, 'a') as accessible_file:
                        accessible_file.write(f'{full_bucket_name} in {region}\n')
            elif result == "Exists but Access Denied":
                print(warning_color + f'Bucket {full_bucket_name} exists in {region}, but access to list contents is denied')
                if output_access_denied:
                    with open(output_access_denied, 'a') as access_denied_file:
                        access_denied_file.write(f'{full_bucket_name} in {region}\n')
            elif result == "Exists but Forbidden":
                print(warning_color + f'Bucket {full_bucket_name} exists in {region}, but it is Forbidden to access')
                if output_forbidden:
                    with open(output_forbidden, 'a') as forbidden_file:
                        forbidden_file.write(f'{full_bucket_name} in {region}\n')
            else:
                print(error_color + f'Bucket {full_bucket_name} does not exist in {region}')

def main():
    parser = argparse.ArgumentParser(description="Check AWS S3 bucket existence")
    parser.add_argument("keyword", help="The word to combine")
    parser.add_argument("--output-accessible", help="Output file for 'Exists and Accessible'")
    parser.add_argument("--output-access-denied", help="Output file for 'Exists but Access Denied'")
    parser.add_argument("--output-forbidden", help="Output file for 'Exists but Forbidden'")
    args = parser.parse_args()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        check_buckets_in_region(args.keyword, args.output_accessible, args.output_access_denied, args.output_forbidden)

if __name__ == "__main__":
    main()
