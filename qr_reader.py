from xml.dom.minidom import parse, parseString
from subprocess import Popen, PIPE

def take_image():
  p = Popen(['fswebcam', '--no-banner', '--greyscale', '-r', '640x480', 'assets/scan.jpg', '-S', '1'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
  output, err = p.communicate()
  if p.returncode == 0:
    return True
  else:
    return False


def read_image():
  p = Popen(['zbarimg', '-q', '--xml', 'assets/scan.jpg'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
  output, err = p.communicate()
  if p.returncode == 0:
    dom = parseString(output)
    nodes = dom.getElementsByTagName('data')
    if nodes.length == 0:
      return False
    return nodes[0].firstChild.data
  else:
    return False


def parse_url(url): 
  #separate address & params
  result = { 'success': True, 'params': {} }
  split = url.split('?')
  #extract address
  address_half = split[0]
  address_split = address_half.split('bitcoin:')
  if len(address_split) == 2:
    result['address'] = address_split[1]
  else:
    return False
  #extract params
  if len(split) > 1:
    params_half = split[1]
    params = params_half.split('&')
    for param in params:
      print param
      pair = param.split('=')
      result['params'][pair[0]] = pair[1] 
  return result


def read_qr():
  pic = take_image()
  if pic:
    result = read_image()
    if (result):
      return parse_url(result)
    else:
      return { 'success': False, 'message': "Failed to find QR code" }
  else:
    return { 'success': False, 'message': "Failed to take image" }
