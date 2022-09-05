#!/usr/bin/env python3
import logging
import os
import datetime
from unicodedata import name

from dotenv import load_dotenv
load_dotenv()

from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)
from google.cloud import storage

# Configure debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Example dates
today = datetime.date.today()

# Initiates GCS client and bucket
storage_client = storage.Client()
bucket = storage_client.bucket(os.environ.get("BUCKET"))



try:
    # API

    ## Initialize Garmin garmin with your credentials
    garmin = Garmin(os.environ.get("GARMIN_EMAIL"), os.environ.get("GARMIN_PW"))

    ## Login to Garmin Connect portal
    garmin.login()

    # USER INFO

    # Get full name from profile
    logger.info(garmin.get_full_name())

    ## Get unit system from profile
    logger.info(garmin.get_unit_system())


    # ACTIVITIES

    # Get activities data from start and limit
    activities = garmin.get_activities(0,5) # 0=start, 1=limit
    #logger.info(activities)
    

    ## Download an Activity
    for activity in activities:

        activity_id = activity["activityId"]
        logger.info("garmin.download_activities(%s)", activity_id)

        gpx_data = garmin.download_activity(activity_id, dl_fmt=garmin.ActivityDownloadFormat.GPX)
        output_file = f"{str(activity_id)}.gpx"

        #checks if file to download already exists in bucket, downloads from Garmin if not
        blob_check = bucket.blob(output_file)
        if (blob_check.exists()):
            print(f"{output_file} already found in bucket...skipping.")
            continue
        else:
            #write file to local disk before upload to GCS
            with open(output_file, "wb") as fb:
                fb.write(gpx_data)
            try:
                upload_blob = bucket.blob(output_file)
                upload_blob.upload_from_filename(output_file)
                logger.info(f"Successfully uploaded {output_file} to bucket")
            except:
                logger.error(f"Failed to upload {output_file} to bucket")
            # Delete local file after success 
            os.remove(output_file)

            
    ## Logout of Garmin Connect portal
    garmin.logout()

except (
        GarminConnectConnectionError,
        GarminConnectAuthenticationError,
        GarminConnectTooManyRequestsError,
    ) as err:
    logger.error("Error occurred during Garmin Connect communication: %s", err)