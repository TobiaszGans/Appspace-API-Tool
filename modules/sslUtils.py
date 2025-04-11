from OpenSSL import SSL, crypto
import socket
from urllib.parse import urlparse

def getPEMFile(reqUrl, port=443):
    ctx = SSL.Context(SSL.SSLv23_METHOD)
    s = socket.create_connection((reqUrl, port))
    s = SSL.Connection(ctx, s)
    s.set_connect_state()
    s.set_tlsext_host_name(str.encode(reqUrl))

    s.sendall(str.encode('HEAD / HTTP/1.0\n\n'))

    peerCertChain = s.get_peer_cert_chain()
    pemFile = ''

    for cert in peerCertChain:
        pemFile += crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8")

    return pemFile

def generateCert(urlAddress):
    parseUrl = urlparse(urlAddress)
    url = parseUrl.hostname
    cert = getPEMFile(url)
    with open('cert.pem', 'w') as file_object:
        file_object.writelines(cert)
