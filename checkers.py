import requests
import os


# Function to Print Checker Board in Console
def print_board(pieces):
    for p in pieces:
        for q in p:
            if q is None:
                print 0,
            else:
                print q['owner'],
            print " ",
        print ""


# Constants
PAWN_RANK = 1
KING_RANK = 2

PLAYER_ONE = 1
PLAYER_TWO = 2


# Parse Parameters
PARSE_APP_ID = os.environ['PARSE_APP_ID']
PARSE_API_KEY = os.environ['PARSE_API_KEY']

PARSE_URL = 'https://api.parse.com/1/classes/GameState'
PARSE_HEADER = {'X-Parse-Application-Id': PARSE_APP_ID,
                'X-Parse-REST-API-Key': PARSE_API_KEY,
                'Content-Type': 'application/json'
                }


# Load List of Existing Games
def load_all():
    url = PARSE_URL + '?keys=name,objectId,createdAt,updatedAt,currentPlayer&order=-updatedAt'
    response = requests.get(url=url, headers=PARSE_HEADER)
    games = response.json()['results']
    return games


# Create New Game
# Store Data on Parse Servers
def new_game(gamename, password):
    pieces = generate_board()
    first_player = random_player()
    payload = {'name': gamename, 'pWord': password, 'piecesArray': pieces, 'currentPlayer': first_player, 'lastMove': None, 'mustJump': False, 'mustJumpFrom': None}
    response = requests.post(url=PARSE_URL, json=payload, headers=PARSE_HEADER)
    return response.json()['objectId']


# Fill New 8x8 Board With Pieces
def generate_board():
    pieces = []
    for y in range(0, 8):
        pieces_row = []
        for x in range(0, 8):
            if y % 2 == x % 2 and y<3:
                new_piece = {'owner': PLAYER_ONE, 'rank': PAWN_RANK}
            elif y % 2 == x % 2 and y>4:
                new_piece = {'owner': PLAYER_TWO, 'rank': PAWN_RANK}
            else:
                new_piece = None
            pieces_row.append(new_piece)
        pieces.append(pieces_row)
    return pieces


# Load Game State From Parse
def load_game(game_id):
    response = requests.get(url=PARSE_URL + '/' + game_id, headers=PARSE_HEADER)
    game_state = response.json()
    return game_state


# Update Game State On Parse
def update_game(game_id, payload):
    response = requests.put(url=PARSE_URL + '/' + game_id, json=payload, headers=PARSE_HEADER)


# Delete a piece from game
def remove_piece(game_state, pos_xy):
    pieces = game_state['piecesArray']

    x = pos_xy[0]
    y = pos_xy[1]
    # Sanity check
    if pieces[y][x] is None:
        #Something's wrong
        pass
    else:
        pieces[y][x] = None


# Check for promotion
def can_promote(game_state, pos_xy):
    pieces = game_state['piecesArray']

    x = pos_xy[0]
    y = pos_xy[1]

    p = pieces[y][x]
    # Sanity check
    if p is None:
        pass
    else:
        if p['rank'] == PAWN_RANK:
            if (p['owner'] == PLAYER_ONE and y==7) or (p['owner'] == PLAYER_TWO and y==0):
                game_state['piecesArray'][y][x]['rank'] = KING_RANK


# Promote a piece to King
def promote_piece(game_state, pos_xy):
    pieces = game_state['piecesArray']

    x = pos_xy[0]
    y = pos_xy[1]

    p = pieces[y][x]
    # Sanity check
    if p is None:
        pass
    else:
        game_state['piecesArray'][y][x]['rank'] = KING_RANK


# Move Piece In Place - Assumes Move is Valid
def move_piece(game_state, move_set):
    pieces = game_state['piecesArray']

    # Extract (x1,y1) (x2,y2) from move_set object
    x1 = move_set['from'][0]
    y1 = move_set['from'][1]
    x2 = move_set['to'][0]
    y2 = move_set['to'][1]

    moving_piece = pieces[y1][x1]
    pieces[y2][x2] = moving_piece
    pieces[y1][x1] = None

    last_move = {'from': [x1,y1], 'to': [x2,y2]}
    game_state['piecesArray'] = pieces
    game_state['lastMove'] = last_move


# Change Turns
def change_turns(game_state):
    player = game_state['currentPlayer']
    if player == PLAYER_ONE:
        player = PLAYER_TWO
    elif player == PLAYER_TWO:
        player = PLAYER_ONE
    else:
        pass # Error
    game_state['currentPlayer'] = player


# Game Over Check
def is_game_over(game_state):
    pieces = game_state['piecesArray']
    p1_count, p2_count = 0, 0

    for rows in pieces:
        for p in rows:
            if p is not None:
                if p['owner']==PLAYER_ONE:
                    p1_count += 1
                elif p['owner']==PLAYER_TWO:
                    p2_count += 1

    if p1_count==0 or p2_count==0:
        # Game over. Set current player to 0 to let front end know
        game_state['currentPlayer'] = 0


# Pick Who Gets First Move
def random_player():
    # To-Do: Randomize Lol
    return PLAYER_ONE


# Check if x,y is Within Game Boundary
def within_bounds(x, y):
    if x<0 or x>7 or y<0 or y>7:
        return False
    else:
        return True


# Get Position of Middle Piece Being Jumped Over
def get_mid(xy1, xy2):
    x1 = xy1[0]
    y1 = xy1[1]
    x2 = xy2[0]
    y2 = xy2[1]

    x_ = x2 - x1
    y_ = y2 - y1

    x_mid = x1 + x_/2
    y_mid = y1 + y_/2

    return [x_mid, y_mid]


# Scan for Jump at pos (x, y)
def can_jump(piecesArray, xy):
    x = xy[0]
    y = xy[1]

    player = piecesArray[y][x]['owner']
    opponent = PLAYER_ONE if player==PLAYER_TWO else PLAYER_TWO
    rank = piecesArray[y][x]['rank']

    # Player ONE moves Down, Player TWO moves Up
    fwd = 1 if player==PLAYER_ONE else -1

    # Checking for jump logic:
    # 1. Make sure target is within bounds
    # 2. Make sure middle space is occupied
    # 3. Make sure it's occupied by opponent
    # 4. Make sure target is empty
    # if All above satisfied return True, can jump.

    # Check for forward jumps x+2, x-2
    if within_bounds(x+2, y+fwd*2):
        if piecesArray[y+fwd][x+1] is not None:
            if piecesArray[y+fwd][x+1]['owner']==opponent:
                if piecesArray[y+fwd*2][x+2] is None:
                    return True
    if within_bounds(x-2, y+fwd*2):
        if piecesArray[y+fwd][x-1] is not None:
            if piecesArray[y+fwd][x-1]['owner']==opponent:
                if piecesArray[y+fwd*2][x-2] is None:
                    return True
    # Check for backward jumps x+2, x-2 if KING
    if rank == KING_RANK:
        if within_bounds(x+2, y-fwd*2):
            if piecesArray[y-fwd][x+1] is not None:
                if piecesArray[y-fwd][x+1]['owner']==opponent:
                    if piecesArray[y-fwd*2][x+2] is None:
                        return True
        if within_bounds(x-2, y-fwd*2):
            if piecesArray[y-fwd][x-1] is not None:
                if piecesArray[y-fwd][x-1]['owner']==opponent:
                    if piecesArray[y-fwd*2][x-2] is None:
                        return True

    # No available jumps found
    return False


# Scan for Jump
def must_jump(piecesArray, player):
    for i in range(0, 8):
        for j in range (0, 8):
            p = piecesArray[i][j]
            if p is not None and p['owner'] == player:
                if can_jump(piecesArray, [j,i]):
                    return True

    # No piece eligible for jump found
    return False


# Higher overloaded level of must_jump
def must_jump_(game_state):
    return must_jump(game_state['piecesArray'],game_state['currentPlayer'])


# Validate Move Before Executing
def valid_move(game_state, move_set):
    pieces = game_state['piecesArray']
    player = game_state['currentPlayer']

    # Extract (x1,y1) (x2,y2) from move_set object
    x1 = move_set['from'][0]
    y1 = move_set['from'][1]
    x2 = move_set['to'][0]
    y2 = move_set['to'][1]

    # Checklist:
    # 0. Check if (x1,y1) and (x2,y2) within boundaries of board
    # 1. Check if piece exists at (x1,y1)
    # 2. Check if empty space exists at (x2,y2)
    # 2.5 Check if piece belongs to player
    # 3. Check if non-king piece is moving forward (player one >0, player two <0)
    # 4. Check if opponent piece is in middle if move is a jump
    # 5. Check if move is a jump if jump is available

    # 6. return True or False

    if x1<0 or x1>7 or y1<0 or y1>7 or x2<0 or x2>7 or y2<0 or y2>7:
        # raise ValueError("Move from %s, %s to %s, %s is out of bounds" % (x1, y1, x2, y2))
        return False

    if pieces[y1][x1] is None:
        # raise ValueError("Piece doesn't exist at %s, %s" % (x1, y1))
        return False

    if pieces[y2][x2] is not None:
        # raise ValueError("There exists a piece already at %s, %s" % (x2, y2))
        return False

    if pieces[y1][x1]['owner'] != player:
        # raise ValueError("Piece being moved does not belong to current player")
        return False

    if pieces[y1][x1]['rank'] == PAWN_RANK:
        if (player == PLAYER_ONE and y2<y1) or (player == PLAYER_TWO and y2>y1):
            # raise ValueError("Pawn piece moving backwards")
            return False

    if abs(y2-y1) == 2:
        mid_pos = get_mid([x1,y1],[x2,y2])
        if pieces[mid_pos[1]][mid_pos[0]] is None:
            # raise ValueError("Jumping over nothing")
            return False

    if must_jump(pieces, player) and abs(y2-y1) == 1:
        # raise ValueError("Move is not a jump - jump is available therefore required")
        return False

    mjf = game_state['mustJumpFrom']
    if mjf is not None:
        if mjf[0] != x1 or mjf[1] != y1:
            # Not jumping from must jump (in a double jump)
            return False

    # No problems found, proceed with move
    return True


def is_jump(from_pos, to_pos):
    x1 = from_pos[0]
    x2 = to_pos[0]
    if abs(x2-x1) == 2:
        return True
    else:
        return False


# Main Execution For Testing Purposes
# g_id = '2ZoCWPTZRF'
# pos1 = [7,3]
# pos2 = [6,2]

# Flow of Updating Game:
#
# g_state = load_game(g_id)
# #if valid_move(g_state, input_move)
# move_piece(g_state, {'from': pos1, 'to': pos2})
# if is_jump(input_move['from'], input_move['to']):
#     dead_piece = get_mid(input_from, input_to)
#     remove_piece(g_state, dead_piece)
#     repeat = can_jump(g_state['piecesArray'], input_to)
# else:
#     repeat = False
# must_jump = False
# must_jump_from = None
# # if repeat == False:
#     # change_turns(g_state)
#     # Check for must jumps
#     # if must jump exists, must_jump = True
# # else: (same player has to jump again, don't change turns)
#     # must_jump = True
#     # must_jump_from = pos2
# g_state['mustJump'] = must_jump
# g_state['mustJumpFrom'] = must_jump_from
# update_game(g_id, g_state)
# print_board(g_state['piecesArray'])


# Execute Move
def perform_turn(g_id, input_move):
    g_state = load_game(g_id)
    if valid_move(g_state, input_move):
        move_piece(g_state, input_move)
        move_from = input_move['from']
        move_to = input_move['to']
        if can_promote(g_state, move_to):
            promote_piece(g_state, move_to)
        # Jump Logic
        if is_jump(move_from, move_to):
            dead_piece = get_mid(move_from, move_to)
            remove_piece(g_state, dead_piece)
            repeat = can_jump(g_state['piecesArray'], move_to)
        else:
            repeat = False
        must_jump_from = None
        if repeat is False:
            change_turns(g_state)
            must_jump_bool = must_jump_(g_state)
            must_jump_from = None
        else:
            must_jump_bool = True
            must_jump_from = move_to
        g_state['mustJump'] = must_jump_bool
        g_state['mustJumpFrom'] = must_jump_from

        is_game_over(g_state)
        update_game(g_id, g_state)
        return g_state
    else:  # Move Invalid
        return g_state
