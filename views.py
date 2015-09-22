from flask import Flask, request, redirect, url_for, render_template, jsonify

import checkers

app = Flask(__name__)


# Main Pages

@app.route('/')
def index():
    return redirect('/checkers')


# BEGIN CHECKERS STUFF
@app.route('/checkers', methods=['GET', 'POST'])
def checkers_home():
    return render_template('checkers.html')


# Create new game, display board and game ID to host
@app.route('/checkers/new-game', methods=['GET', 'POST'])
def checkers_new_game():
    if request.method == 'POST':
        g_id = checkers.new_game()
        # Load game board display with g_id parameter, player=player1
        return redirect('/checkers/load-game/'+g_id+'?player=1')


# Load game, display board and game ID to guest player
@app.route('/checkers/load-game/<gameid>', methods=['GET'])
def checkers_load(gameid):
    g_state = checkers.load_game(gameid)
    if 'error' in g_state:
        flash('The game id is invalid')
        return redirect('/checkers')
    else:
        player = checkers.PLAYER_TWO
        # Allows player to regain access as player ONE if page was lost
        if 'player' in request.args:
            player = int(request.args.get('player'))
            if player!=1 and player!=2:
                player=2
        # Load game board display with g_id as parameter, player=player2
        return render_template('checkers-board.html', gameid=gameid, player=player)


# Polling API Endpoint
@app.route('/checkers/poll/<gameid>', methods=['GET'])
def checkers_poll(gameid):
    if request.method == 'GET':
        g_state = checkers.load_game(gameid)
        if 'error' in g_state:
            # Error
            return "Error"
        else:
            return jsonify(g_state)


# Make Move API Endpoint
@app.route('/checkers/move/<gameid>', methods=['POST'])
def checkers_move(gameid):
    if request.method == 'POST':
        move = request.get_json()
        if 'from' in move and 'to' in move:
            return jsonify(checkers.perform_turn(gameid, move))
        else: # Error
            pass

# END CHECKERS STUFF


if __name__ == '__main__':
    app.debug = True
    app.run()