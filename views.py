from flask import Flask, request, redirect, url_for, render_template, jsonify

import hashlib

import checkers

app = Flask(__name__)


# Main Pages

@app.route('/')
def index():
    return redirect('/checkers')


# BEGIN CHECKERS STUFF
@app.route('/checkers', methods=['GET', 'POST'])
def checkers_home():
    games = checkers.load_all()
    return render_template('checkers.html', games=games)


# Create new game, display board and game ID to host
@app.route('/checkers/new-game', methods=['GET', 'POST'])
def checkers_new_game():
    if request.method == 'POST':
        gamename = request.form.get('gamename')
        password = request.form.get('pwrd')
        if gamename == '' or gamename.isspace():
            return redirect('/checkers')
        if password == '' or gamename.isspace():
            password = None
        else:
            password = hashlib.sha1(password.encode()).hexdigest()
        g_id = checkers.new_game(gamename, password)
        # Load game board display with g_id parameter, player=player1
        return redirect('/checkers/load-game/'+g_id+'?player=1')


# Load game, display board and game ID to guest player
@app.route('/checkers/load-game/<gameid>', methods=['GET', 'POST'])
def checkers_load(gameid):
    g_state = checkers.load_game(gameid)
    if 'error' in g_state:
        return redirect('/checkers')
    if 'player' not in request.args:
        return redirect('/checkers')

    # Get player to join as
    player = int(request.args.get('player'))

    if request.method == 'GET':
        if g_state['pWord'] is not None:
            return render_template('join-game.html', gameid=gameid, player=player)

    if request.method == 'POST':
        password = request.form.get('pwrd')
        if hashlib.sha1(password.encode()).hexdigest() != g_state['pWord']:
            return render_template('join-game.html', gameid=gameid, player=player)

    if player!=1 and player!=2:
        player=2
    # Load game board display with g_id as parameter, chosen player or player 2 default
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