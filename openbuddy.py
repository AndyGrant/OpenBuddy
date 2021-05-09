import chess, chess.pgn
import re, sys, time, io, requests

from discord import Client, File
from discord.ext import commands
from PIL import Image

ASSETS = {}
BOT    = commands.Bot('')

def generate_assets():

    for letter in 'kqrbnpKQRBNP':
        source = 'assets/Chess_{}{}t60.png'.format(letter.lower(), ['d', 'l'][letter.isupper()])
        ASSETS[letter] = Image.open(source)

    ASSETS['board'] = Image.open('assets/board.png').resize((504, 504))

def fen_to_image(fen):

    canvas = Image.new(mode='RGBA', size=(504, 504))
    canvas.paste(ASSETS['board'], (0, 0))

    square = 56
    for ch in fen.split()[0]:

        if ch in '12345678':
            square += int(ch)

        elif ch == '/':
            square -= 16

        else:
            rank = square // 8; file = square % 8
            offset = (12 + 60 * file, 12 + 60 * (7 - rank))
            canvas.paste(ASSETS[ch], offset, mask=ASSETS[ch])
            square = square + 1

    return canvas


@BOT.event
async def on_message(message):
    try:
        if message.author != BOT.user:
            await bot_fen_to_image(message)
            await bot_opening_to_image(message)
            await bot_openbench_test_results(message)
    except:
        pass

async def bot_fen_to_image(message):

    try:
        pattern = '(([1-8kqrbnpKQRBNP]*)/){7}([1-8kqrbnpKQRBNP]*) [wb] [KQkq-]+'

        match = re.search(pattern, message.content)
        board = chess.Board(match.group())
        image = fen_to_image(match.group())

        strify = match.group().split()[0].replace('/', '_')
        fname  = 'outputs/FEN_{}.png'.format(strify)
        image.save(fname); time.sleep(.01)

        await message.reply('', file=File(fname))

    except Exception:
        return

async def bot_opening_to_image(message):

    pattern = "(\d+\.\s*((([BKNQR]?[a-h]?[1-8]?(x)?[a-h][1-8](=)?[NBRQ]?)|(O-O)|(O-O-O))(\+)?\s*(\{.*\}\s*)?){1,2})+"

    match = re.search(pattern, message.content)
    if match == None: return

    sys.stderr = io.StringIO()
    game = chess.pgn.read_game(io.StringIO(match.group()))
    sys.stderr = sys.__stderr__

    board = chess.Board()
    for move in game.mainline_moves():
        board.push(move)

    image  = fen_to_image(board.fen())
    strify = board.fen().split()[0].replace('/', '_')
    fname  = 'outputs/FEN_{}.png'.format(strify)
    image.save(fname); time.sleep(.01)

    await message.reply(board.fen(), file=File(fname))

async def bot_openbench_test_results(message):

    try:
        pattern = 'http://chess.grantnet.us/test/[0-9].*'
        match   = re.search(pattern, message.content)
        html    = str(requests.get(match.group()).content)

        pattern = '(?<=<th>Engine</th><td>)[a-zA-Z]*</td>'
        engine  = re.search(pattern, html).group().split('<')[0]

        pattern = '(?<=<th>Dev Branch</th><td>)[^<]*</td>'
        dev     = re.search(pattern, html).group().split('<')[0]

        pattern = '(?<=<th>Base Branch</th><td>)[^<]*</td>'
        base    = re.search(pattern, html).group().split('<')[0]

        pattern = '(?<=<pre>).*</pre>'
        block   = re.search(pattern, html, re.DOTALL).group().rstrip('</pre>')
        block   = block.replace('<br/>', '\n')

        response = "**{}**: {} _vs_ {}\n```\n{}\n```".format(engine, dev, base, block)
        await message.channel.send(response)

    except Exception as error:
        return


with open('token.txt') as fin:
    generate_assets()
    BOT.run(fin.read())

