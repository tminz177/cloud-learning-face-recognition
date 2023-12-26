import boto3
import os
import json

dynamodb = boto3.client('dynamodb', region_name = 'ap-northeast-1')
rekognition=boto3.client('rekognition', region_name = 'ap-northeast-1')

collection_id = os.environ['COLLECTION_ID']
table_name = os.environ['TableName']


def lambda_handler(event, context):
    #get URI from UI
    uri = event['uri']
    
    #Search face in collection
    faces = rekognition_search_faces(uri)
    
    #Get OBJ from DB
    db = dynamoDB_search(faces)
    
    #Create Obj to response
    obj = obj_response(db, faces)
    
    response = {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(faces)
    }    
    return response
   

def rekognition_search_faces(uri):
    uri = uri.split("/")
    bucket= uri[2]
    collectionId = collection_id
    fileName= uri[3] + "/" +uri[4]
    threshold = 70
    maxFaces=5
    response = rekognition.search_faces_by_image(
        CollectionId=collectionId,
        Image={'S3Object':{'Bucket':bucket,'Name':fileName}},
        FaceMatchThreshold=threshold,
        MaxFaces=maxFaces)
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        face_matches = response['FaceMatches']
        faces = [match['Face'] for match in face_matches]
        return faces
    return None
        
def dynamoDB_search(faces):
    # Extract FaceIds from the list of faces
    face_ids = [face['FaceId'] for face in faces]

    query_params = {
        'TableName': table_name,
        'KeyConditionExpression': 'FaceId IN (:pk_values)',
        'ExpressionAttributeValues': {
            ':pk_values': face_ids
        }
    }

    try:
        response = dynamodb.query(**query_params)

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print("DynamoDB Query Result:", response['Items'])
            return response['Items']

    except Exception as e:
        print(f"Error querying DynamoDB: {e}")

    return None
        
class obj_to_response:
    def __init__(self, faceId, bounding_box, name, uri):
        self.faceId = faceId 
        self.bounding_box = bounding_box 
        self.name = name 
        self.uri = uri 

def obj_response(db, re):
    list_response = []

    # Check if db is not None before iterating
    if db:
        for i in db:
            for y in re:
                if i['FaceID'] == y['FaceId']:
                    list_response.append(
                        obj_to_response(
                            i['FaceID'], y['BoundingBox'], i['Name'], i['BucketLocation']
                        )
                    )
                    break

    print("List Response:", list_response)
    return list_response      




  