import logging
import pandas as pd
from db_manager.augur_manager import AugurManager
from app import celery_app
from cache_manager.cache_manager import CacheManager as cm
import io
import datetime as dt
from sqlalchemy.exc import SQLAlchemyError

"""
TODO:
 - (1) update QUERY_NAME
 - (2) update 'bus_factor_query' found in function definition and in the function call that sets the 'ack' variable below.
    'NAME' should be the same as QUERY_NAME
(3) paste SQL query in the query_string
 - (4) insert any necessary df column name or format changed under the pandas column and format updates comment
(5) reset df index if #4 is performed via "df = df.reset_index(drop=True)"
(6) go to index/index_callbacks.py and import the bus_factor_query as a unqiue acronym and add it to the QUERIES list
(7) delete this list when completed
"""

QUERY_NAME = "release_frequencey"


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    exponential_backoff=2,
    retry_kwargs={"max_retries": 5},
    retry_jitter=True,
)
def release_frequencey_query(self, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database for contributor data.

    Args:
    -----
        repo_ids ([str]): repos that SQL query is executed on.

    Returns:
    --------
        dict: Results from SQL query, interpreted from pd.to_dict('records')
    """
    logging.warning(f"{QUERY_NAME}_DATA_QUERY - START")

    if len(repos) == 0:
        return None

    query_string = f"""
                SELECT DATE_TRUNC('month', release_created_at)::date AS created,
                COUNT(*) AS total_releases, repo_id as id
                FROM augur_data.releases
                WHERE release_is_draft = false
                AND
                repo_id in ({str(repos)[1:-1]})
                GROUP BY created,id
                LIMIT 20;
                    """
                    # repo_id in ({str(repos)[1:-1]})

    try:
        dbm = AugurManager()
        engine = dbm.get_engine()
    except KeyError:
        # noack, data wasn't successfully set.
        logging.error(f"{QUERY_NAME}_DATA_QUERY - INCOMPLETE ENVIRONMENT")
        return False
    except SQLAlchemyError:
        logging.error(f"{QUERY_NAME}_DATA_QUERY - COULDN'T CONNECT TO DB")
        # allow retry via Celery rules.
        raise SQLAlchemyError("DBConnect failed")

    df = dbm.run_query(query_string)

    # pandas column and format updates
    #Commonly used df updates:

    #df["creted_month"] = df["created_month"].astype(str)  # contributor ids to strings
    #df["created_month"] = df["created_month"].str[:15]
    df = df.sort_values(by="created")
    # df = df.reset_index()
    # df = df.reset_index(drop=True)

    # change to compatible type and remove all data that has been incorrectly formated
    #df["created_month"] = pd.to_datetime(df["created_month"], utc=True).dt.date
    #df = df[df.created < dt.date.today()]

    pic = []

    for i, r in enumerate(repos):
        # convert series to a dataframe
        c_df = pd.DataFrame(df.loc[df["created"] == r]).reset_index(drop=True)

        # bytes buffer to be written to
        b = io.BytesIO()

        # write dataframe in feather format to BytesIO buffer
        bs = c_df.to_feather(b)

        # move head of buffer to the beginning
        b.seek(0)

        # write the bytes of the buffer into the array
        bs = b.read()
        pic.append(bs)

    del df

    # store results in Redis
    cm_o = cm()

    # 'ack' is a boolean of whether data was set correctly or not.
    ack = cm_o.setm(
        func= release_frequencey_query,
        repos=repos,
        datas=pic,
    )
    logging.warning(f"{QUERY_NAME}_DATA_QUERY - END")
    
    print("ACK" , ack)

    return ack