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
        'body': json.dumps(obj)
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
        faces = [
            {'FaceId': match['Face']['FaceId'], 'BoundingBox': match['Face']['BoundingBox'],
             'Similarity': match['Similarity']} for match in face_matches]
        return faces
    return None
        
def dynamoDB_search(faces):
    # Extract FaceIds from the list of faces
    face_ids = [face['FaceId'] for face in faces]

    try:
        response = dynamodb.scan(
            TableName=table_name,
            FilterExpression='FaceID IN (' + ', '.join([':id' + str(i) for i in range(len(face_ids))]) + ')',
            ExpressionAttributeValues={':id' + str(i): {'S': face_id} for i, face_id in enumerate(face_ids)}
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print("DynamoDB Query Result:", response['Items'])
            return response['Items']

    except Exception as e:
        print(f"Error querying DynamoDB: {e}")

    return None
        
class obj_to_response:
    def __init__(self, faceId, bounding_box, similarity, name, uri):
        self.faceId = faceId 
        self.bounding_box = bounding_box 
        self.similarity = similarity
        self.name = name 
        self.uri = uri 

def obj_response(db, re):
    list_response = []

    # Check if db is not None before iterating
    if db:
        for i in db:
            dynamoDB_face_id = i['FaceID']['S']  # Extract the actual FaceID value from DynamoDB

            for y in re:
                rekognition_face_id = y['FaceId']

                if dynamoDB_face_id == rekognition_face_id:
                    list_response.append({
                        'faceId': dynamoDB_face_id,
                        'bounding_box': y['BoundingBox'],
                        'similarity': y['Similarity'],
                        'name': i['Name'],
                        'uri': i['BucketLocation']
                    })
                    break

    print("List Response:", list_response)
    return list_response




  