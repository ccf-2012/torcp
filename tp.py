from torcp.torcp import Torcp
import logging.handlers
import logging, os


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,  format='%(asctime)s  %(message)s')
    # logging.basicConfig(level=logging.INFO,  format='%(asctime)s %(levelname)s %(funcName)s %(message)s')
    # logging.basicConfig(
    #     filename=os.path.join(os.getcwd(), "torcp.log"),
    #     level=logging.INFO,
    #     format='%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s',
    #     datefmt='%Y-%m-%d %H:%M:%S',
    # )

    o = Torcp()
    o.main()
