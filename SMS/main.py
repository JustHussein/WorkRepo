import logging
import connection
import send_sms
import datetime
import argparse

# logging part
current_date = datetime.date.today().strftime("%Y%m%d")
log_filename = f".\\SMSLog\\SMSLog_{current_date}.log"
logging.basicConfig(filename=log_filename,
                    encoding='utf-8',
                    level=logging.DEBUG,
                    format='%(levelname)s:%(asctime)s:%(message)s')


if __name__ == "__main__":

    logger = logging.getLogger("main")

    try:
        parser = argparse.ArgumentParser(
            description="A query with command-line arguments")

        parser.add_argument('query', type=str, help="query")
        args = parser.parse_args()
    except:
        logger.error("query is not valid")

    logger.debug('Started!')

    rows = connection.excute_query(args.query)

    if rows:
        send_sms.send_message(rows)

    else:
        logger.debug('Nothing To Send!')

    logger.debug("Finished!")
