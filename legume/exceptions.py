class LegumeError(Exception): pass
class ArgumentError(LegumeError): pass
class NetworkEndpointError(LegumeError): pass
class PacketDataError(LegumeError): pass
class ServerError(LegumeError): pass
class ClientError(LegumeError): pass
class MessageError(LegumeError): pass
class BufferError(LegumeError): pass
