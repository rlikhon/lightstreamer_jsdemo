#!/usr/bin/env python
'''An example of Lightstreamer remote Chat Adapter, which enables the exchange
of messages sent by users accessing the client Chat Application demo.
'''
import logging
import time
import argparse
import ssl
from threading import Lock
from lightstreamer_adapter.interfaces.metadata import (MetadataProvider,
                                                       NotificationError)
from lightstreamer_adapter.interfaces.data import DataProvider, SubscribeError
from lightstreamer_adapter.server import (DataProviderServer,
                                          MetadataProviderServer)


# The name of the item to subscribe to.
ITEM_NAME = "chat_room"


class ChatMetadataAdapter(MetadataProvider):
    """Subclass of MetadataProvider which provides a specific implementation
    to manage user sessions and user messages.
    """

    def __init__(self, data_adapter):
        self.log = logging.getLogger("LS_demos_Logger.chat")
        # Reference to the provided ChatDataAdapter, which will be used to send
        # messages to pushed to the browsers.
        self.data_adapter = data_adapter

        # Dictionary to keep client context information supplied by
        # Lightstreamer on new session notifications.
        self.sessions = {}
        # Lock used to manage concurrent access to the sessions dictionary.
        self.sessions_lock = Lock()

    def initialize(self, parameters, config_file=None):
        """Invoked to provide initialization information to the
        ChataMetadataAdapter."""
        self.log.info("ChatMetadataAdapter ready")

    def notify_user_message(self, user, session_id, message):
        """Triggered by a client 'sendMessage' call.
        The message encodes a chat message from the client.
        """
        if message is None:
            self.log.warning("None message received")
            raise NotificationError("None message received")

        # Message must be in the form "CHAT|<message>".
        msg_tokens = message.split('|')
        if len(msg_tokens) != 2 or msg_tokens[0] != "CHAT":
            self.log.warning("Wrong message received")
            raise NotificationError("Wrong message received")

        # Retrieves the user session info associated with the session_id.
        with self.sessions_lock:
            session_info = self.sessions.get(session_id)
            if session_info is None:
                raise NotificationError(("Session lost! Please reload the "
                                         "browser page(s)."))

        # Extracts from the info the IP and the user agent, to identify the
        # originator of the # message.
        ipaddress = session_info["REMOTE_IP"]
        user_agent = session_info["USER_AGENT"]

        # Sends the message to be pushed to the browsers.
        self.data_adapter.send_message(ipaddress, user_agent, msg_tokens[1])

    def notify_session_close(self, session_id):
        # Discard session information
        with self.sessions_lock:
            del self.sessions[session_id]

    def notify_new_session(self, user, session_id, client_context):
        # Register the session details.
        with self.sessions_lock:
            self.sessions[session_id] = client_context


class ChataDataAdapter(DataProvider):
    """Implementation of the DataProvider abstract class, which pushes messages
    sent by users to the unique chat room, managed through the unique item
    'chat_room'.
    """

    def __init__(self):
        self.log = logging.getLogger("LS_demos_Logger.chat")
        self.subscribed = None

        # Reference to the provided ItemEventListener instance
        self.listener = None

    def initialize(self, params, config_file=None):
        """Caches the reference to the provided ItemEventListener instance."""
        self.log.info("ChatDataAdapter ready")

    def set_listener(self, listener):
        self.listener = listener

    def subscribe(self, item_name):
        """Invoked to request data for the item_name item."""
        if item_name == ITEM_NAME:
            self.subscribed = item_name
        else:
            # Only one item for a unique chat room is managed.
            raise SubscribeError("No such item")

    def unsubscribe(self, item_name):
        """Invoked to end a previous request of data for an item."""
        self.subscribed = None

    def issnapshot_available(self, item_name):
        """Invoked to provide initialization information to the Data Adapter.
        This adapter does not handle the snapshot.
        If there is someone subscribed the snapshot is kept by the server.
        """
        return False

    def send_message(self, ipaddress, nick, message):
        """Accepts message submission for the unique chat room.
        The sender is identified by an ipaddress address and a nickname.
        """
        if not message:
            self.log.warning("Received empty or None message")
            return False

        if not nick:
            self.log.warning("Received empty or None nick")
            return False

        if not ipaddress:
            self.log.warning("Received empty or None ipaddress")
            return False

        # Gets the current timestamp
        now = time.time()

        # Gets both the raw and the formatted version of the current timestamp.
        raw_timestamp = str(int(round(now * 1000)))
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        self.log.debug("%s|New message: %s -> %s -> %s", timestamp, ipaddress,
                       nick, message)

        # Fills the events dictionary object.
        update = {"IP": ipaddress, "nick": nick, "message": message,
                  "timestamp": timestamp,
                  "raw_timestamp": raw_timestamp}

        # Sends the events.
        self.listener.update(self.subscribed, update, False)


def main():
    '''Module Entry Point'''
    logging.basicConfig(datefmt='%m/%d/%Y %I:%M:%S %p',
                        format='%(asctime)s %(levelname)-7s %(message)s',
                        level=logging.DEBUG)

    parser = argparse.ArgumentParser(description=("Launch the Remote Chat "
                                                  "Adapter."))
    parser.add_argument('--host', type=str, nargs='?', metavar='<host>',
                        default="localhost", help=("the host name or ip "
                                                   "address of LS server"))
    parser.add_argument('--tls', action='store_true',
                        help=("use encrypted communications"))
    parser.set_defaults(tls=False)
    parser.add_argument('--user', type=str, metavar='<user>',
                        required=False, help=("the username credential to be "
                                              "sent to the Proxy Adapter"))
    parser.add_argument('--password', type=str, metavar='<password>',
                        required=False, help=("the password credential to be "
                                              "sent to the Proxy Adapter"))
    parser.add_argument('--metadata_rrport', type=int, metavar='<port>',
                        required=True, help=("the request/reply tcp port "
                                             "number where the Proxy Metadata "
                                             "Adapter is listening on"))
    parser.add_argument('--data_rrport', type=int, metavar='<port>',
                        required=True, help=("the request/reply tcp port "
                                             "where the Proxy DataAdapter is "
                                             "listening on"))
    parser.add_argument('--data_notifport', type=int, metavar='<port>',
                        required=True, help=("the notify tcp port where the "
                                             "Proxy DataAdapter is listening "
                                             "on"))
    args = parser.parse_args()

    # Creates a new instance of the ChatDataAdapter.
    data_adapter = ChataDataAdapter()

    # Creates a new instance of ChatMetadataAdapter and pass data_adapter to it.
    metadata_adaper = ChatMetadataAdapter(data_adapter)

    context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile="push_mycompany_com.cer") if args.tls is True else None
    # context = ssl._create_unverified_context(purpose=ssl.Purpose.SERVER_AUTH) if args.tls is True else None

    # Creates the MetadataProviderServer, passing to it metadata_adaper and the
    # tuple containing the target host information.
    metadata_provider_server = MetadataProviderServer(metadata_adaper,
                                                      (args.host,
                                                       args.metadata_rrport),
                                                      ssl_context=context)

    # Creates the DataProviderServer, passing to it data_adapter and the tuple
    # containing the target host information.
    dataprovider_server = DataProviderServer(data_adapter,
                                             (args.host,
                                              args.data_rrport,
                                              args.data_notifport),
                                             keep_alive=0,
                                             ssl_context=context)

    if args.user is not None and args.password is not None:
        metadata_provider_server.remote_user = args.user
        metadata_provider_server.remote_password = args.password
        dataprovider_server.remote_user = args.user
        dataprovider_server.remote_password = args.password

    # Starts the MetadataProviderServer and the DataProviderServer
    metadata_provider_server.start()
    dataprovider_server.start()


if __name__ == "__main__":
    main()
