import pymongo
import boto3
import os
from botocore.exceptions import NoCredentialsError
from datetime import datetime 
import uuid
import json
from botocore.exceptions import NoCredentialsError, ClientError




class S3_file_Upload:
    def __init__(self, bucket_name, aws_access_key, aws_secret_key, region_name='us-east-1'):
        self.bucket_name = bucket_name
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region_name
        )
        self.region = region_name

    def upload_image(self, main_event, sub_event, files):
        try:
            # Ensure main_event and sub_event are not empty
            if not main_event or not sub_event:
                print("Event or Sub-event names cannot be empty.")
                return None

            if not files:
                print("No files to upload.")
                return None

            urls = []
            for image in files:
                if not image.filename:
                    print("File has no name, skipping.")
                    continue  # Skip empty files or files with no name
                
                filename = image.filename  # Get the image's filename (from the file object)
                s3_key = f"{main_event}/{sub_event}/{filename}"

                # Upload the image directly to S3
                try:
                    self.s3.upload_fileobj(image, self.bucket_name, s3_key)
                    # Build the file URL
                    url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
                    print(url)
                    urls.append(url)
                except ClientError as e:
                    print(f"Failed to upload {filename}: {e}")
                    continue  # Continue with other files
                except Exception as e:
                    print(f"Error uploading {filename}: {e}")
                    continue  # Continue with other files

            return urls if urls else None

        except NoCredentialsError:
            print("AWS credentials are not available.")
            return None
        except Exception as e:
            print(f"General error: {e}")
            return None

    def save_main(self, main_event):
        """
        Save the main event as a JSON object into S3 inside 'events/' folder
        """
        try:
            # S3 key
            key = f"events/{main_event}.json"
            
            # Prepare JSON data
            data = {
                "event_name": main_event
            }
            
            # Upload the JSON directly
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(data),
                ContentType='application/json'
            )
            
            # Build the file URL
            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
            
            return url

        except NoCredentialsError:
            print("Credentials not available")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def list_images(self,main_event,sub_event):
        s3_prefix = f"{main_event}/{sub_event}/"
        
        # Use Boto3 to list the objects under this prefix (event_name/sub_event_name)
        s3_client = boto3.client('s3')
        response = s3_client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=s3_prefix
        )

        if 'Contents' in response:
            # Extract the URLs of the images
            photos = []
            for obj in response['Contents']:
                photo_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{obj['Key']}"
                photos.append(photo_url)

            return photos
        else:
            return None
    
class MongoDb_:
    def __init__(self,url,database,event_collection,persons_collection):
        client = pymongo.MongoClient(url)
        self.database = client[database]
        self.event_collection = self.database[event_collection]
        self.person_collection = self.database[persons_collection]


    def person_info(self,id,image_array):

        data = {
            "person_id": id,
            "person_name" :None,
            "images_present" : image_array
        }


    def image_info(self,image_person_mapping):
        all_data = []
        for file_name,person_ids in image_person_mapping.item():
            data = {
                "file_name": f"{file_name}_{uuid.uuid4()}",
                "person_ids" : person_ids,
                "uploaded_at" : datetime.now(),
            }
            all_data.append(data)
        self.persons_collection.insert_many(all_data)

    def list_main_event(self):
        cursor = self.event_collection.find({}, {"main_event.event": 1, "_id": 0})
        events = [doc['main_event']['event'] for doc in cursor if 'main_event' in doc and 'event' in doc['main_event']]
        return events
    
    def save_event(self, main_event):
        # Check if the event is present in the collection
        query = {"main_event.event": main_event}  # Adjusted query to match the schema
        response = self.event_collection.find_one(query)
        
        if not response:
            # If the event is not found, create a new event with the main_event structure
            self.event_collection.insert_one({
                "main_event": {
                    "event": main_event,
                    "sub_event": None
                }
            })
            # Set the main_event after insertion
            return main_event
        else:
            # If the event is found, return the event from the existing document
            return response["main_event"]["event"]
    
    def add_sub_event(self, main_event, sub_event):
    # Check if the main event exists
        query = {"main_event.event": main_event}
        response = self.event_collection.find_one(query)
        
        if response:
            # Event exists, now update sub_event list
            existing_sub_events = response["main_event"].get("sub_event", [])
            
            if existing_sub_events is None:
                existing_sub_events = []
            
            # Add only if sub_event is not already present
            if sub_event not in existing_sub_events:
                existing_sub_events.append(sub_event)
                
                # Update the document
                self.event_collection.update_one(
                    {"_id": response["_id"]},
                    {"$set": {"main_event.sub_event": existing_sub_events}}
                )
        else:
            # Event does not exist, create it with the sub_event inside a list
            self.event_collection.insert_one({
                "main_event": {
                    "event": main_event,
                    "sub_event": [sub_event]
                }
            })
    def get_sub_events(self, main_event):
        # Find the main_event document
        query = {"main_event.event": main_event}
        response = self.event_collection.find_one(query)
        
        if response:
            # Fetch the list of sub-events
            sub_events = response["main_event"].get("sub_event", [])
            
            if sub_events is None:
                sub_events = []
            
            return sub_events
        else:
            # If main_event not found, return empty list
            return []