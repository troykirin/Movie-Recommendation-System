import math

NUM_NEAREST_NEIGHBORS = 10
TRAINING_DATA_MATRIX = []  # 200x1000 matrix of training data
USER_DATA_DICTIONARY = {}  # Dictionary of all unfiltered user data {201: [[237,4],[306,5], ...], 202: [[]] ... }

cosine_similarity = []  # 200x100 matrix of cosine similarities

# TODO: MAKE ALL OPERATIONS IN FLOATS
# Parse train.txt to place into 2D matrix
with open("train.txt") as openfileobject:
    for line in openfileobject:
        line = line.split("\t")  # Split text file by tabs
        raw_movie_ratings = line

        # Change all items in array of ratings to integers and remove '\n' character
        filtered_movie_ratings = []
        for movie_rating in raw_movie_ratings:
            filtered_movie_ratings.append(int(movie_rating.rstrip()))

        TRAINING_DATA_MATRIX.append(filtered_movie_ratings)


# Parse test5.txt and place into user_data_dictionary
with open("test5.txt") as openfileobject:
    USER_PREDICTION_MIN_ID = 201
    USER_PREDICTION_MAX_ID = 301

    for line in openfileobject:
        line = line.replace("\r\n", "")
        line = line.split(" ")
        if not int(line[0]) in USER_DATA_DICTIONARY:
            USER_DATA_DICTIONARY[int(line[0])] = [[int(line[1]), int(line[2])]]
        else:
            current_ratings = USER_DATA_DICTIONARY[int(line[0])]
            current_ratings += [[int(line[1]), int(line[2])]]


# ------------------------------------- Preprocessing Training and User Data -------------------------------------------
# Calculate the cosine similarity and find the nearest neighbors between every single user and the training data
for user_id in range(USER_PREDICTION_MIN_ID, USER_PREDICTION_MAX_ID):
    filtered_user_data_dictionary = {}  # {"movie id" : "movie rating", ...}

    # Gather rating information about user
    for user_data in USER_DATA_DICTIONARY[user_id]:
        if user_data[1] != 0:
            filtered_user_data_dictionary[user_data[0]] = user_data[1]  # All zeros removed from user data

    # Calculate this user's similarity against 200 entries of training data
    single_user_cosine_similarity = []
    single_user_nearest_neighbors = []
    for training_data_id in range(0, 200):
        similarity = 0
        user_normalize = 0
        training_normalize = 0
        mutually_rated_movies = []

        # Find all mutually rated movies
        for movie_id in filtered_user_data_dictionary:
            training_rating = TRAINING_DATA_MATRIX[training_data_id][movie_id-1]
            if training_rating != 0:
                mutually_rated_movies.append(movie_id)

        # Handle cases in which there is only 0 or 1 similar movie
        if len(mutually_rated_movies) == 0:
            single_user_cosine_similarity.append(0.0001)
            continue
        elif len(mutually_rated_movies) == 1:
            # Use custom formula to calculate a pseudo cosine similarity
            training_rating = TRAINING_DATA_MATRIX[training_data_id][mutually_rated_movies[0]-1]
            user_rating = filtered_user_data_dictionary[mutually_rated_movies[0]]
            pseudo_cos_similarity = (1/(abs(training_rating-user_rating)+1))  # 1/(difference + 1)

            # Cannot let a cosine similarity reach a value of 1  # TODO: Needs better algorithm
            if pseudo_cos_similarity == 1:
                pseudo_cos_similarity = 0.95

            single_user_cosine_similarity.append(pseudo_cos_similarity)
            continue

        # Calculate similarity and normalizing measurements between user and training data
        for movie_id in mutually_rated_movies:
            training_rating = TRAINING_DATA_MATRIX[training_data_id][movie_id-1]
            similarity += (int(training_rating) * filtered_user_data_dictionary[movie_id])
            user_normalize += (int(filtered_user_data_dictionary[movie_id]) ** 2)
            training_normalize += (int(training_rating) ** 2)

        # Normalize the cosine similarity
        normalize = math.sqrt(user_normalize) * math.sqrt(training_normalize)
        cos_similarity = similarity / normalize

        # Append to list of user's cosine similarities against test data
        single_user_cosine_similarity.append(cos_similarity)

    # print single_user_cosine_similarity  # Should be 200 in length
    cosine_similarity.append(single_user_cosine_similarity)

print cosine_similarity  # Should be 100 in length


# --------------------------------------- Rating Prediction For All Users ----------------------------------------------
f = open("test_.txt", "a+")
for user_id in range(USER_PREDICTION_MIN_ID, USER_PREDICTION_MAX_ID):

    # Look through every single user's previous ratings and predictions that need to be completed
    for user_data in USER_DATA_DICTIONARY[user_id]:

        # Identify all data that needs to be predicted
        if user_data[1] == 0:
            numerator = 0
            denominator = 0
            movie_id_of_to_be_predicted = user_data[0]
            mutually_rated_movies = []
            nearest_neighbors = []

            # Find all users that have also rated this movie
            for training_data_id in range(0, 200):
                if TRAINING_DATA_MATRIX[training_data_id][movie_id_of_to_be_predicted-1] != 0:
                    mutually_rated_movies.append(training_data_id)

            # Calculate nearest neighbors considering all users who have rated the movie we are trying to predict
            for mutually_rated_movie_id in mutually_rated_movies:  # TODO: If Cosine Similarity is less than 0.5, do not even append
                mutually_rated_movie_user_cos_sim = cosine_similarity[user_id - USER_PREDICTION_MIN_ID][
                    mutually_rated_movie_id - 1]
                if len(nearest_neighbors) > NUM_NEAREST_NEIGHBORS:
                    if mutually_rated_movie_user_cos_sim > nearest_neighbors[0]['cos_sim']:
                        nearest_neighbors.pop(0)
                        nearest_neighbors.append(
                            {'id': mutually_rated_movie_id, 'cos_sim': mutually_rated_movie_user_cos_sim})
                        nearest_neighbors = sorted(nearest_neighbors, key=lambda k: k['cos_sim'])
                else:
                    nearest_neighbors.append(
                        {'id': mutually_rated_movie_id, 'cos_sim': mutually_rated_movie_user_cos_sim})
                    nearest_neighbors = sorted(nearest_neighbors, key=lambda k: k['cos_sim'])

            # print nearest_neighbors  # TODO: There are still Cosine Similarities of 0?!

            # Iterate through all of nearest neighbors to calculate using mutually rated movies
            for neighbor in nearest_neighbors:
                neighbor_movie_rating = TRAINING_DATA_MATRIX[neighbor['id']-1][movie_id_of_to_be_predicted-1]
                if neighbor_movie_rating != 0:
                    numerator += (int(neighbor['cos_sim']) * neighbor_movie_rating)
                    denominator += int(neighbor['cos_sim'])

            # If no neighbors rated this movie, set the movie prediction to that of the highest similarity
            if denominator == 0:
                # id_of_most_similar_movie = nearest_neighbors.pop(len(nearest_neighbors)-1)['id']
                # movie_prediction = nearest_neighbors.pop(len(nearest_neighbors)-1)['id']
                movie_prediction = -1
            else:
                movie_prediction = numerator/denominator

            f.write(str(user_id) + " " + str(movie_id_of_to_be_predicted) + " " + str(movie_prediction) + "\n")
