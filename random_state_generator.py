import random
from state import BlocksState

def generate_state(N, seed=42):
    random.seed(seed)
    state = []
    klocki = list(range(1, N + 1))
    random.shuffle(klocki)

    top_blocks = [0]*N
    miejsc = 0
    for klocek in klocki:
        pozycja = random.randint(0, miejsc)
        # taka sama szansa położenia na każdej górce ( i stole)
        if pozycja == miejsc:
            miejsc += 1
        # na wylosowanej pozycji był klocek z topblocks
        state.append(top_blocks[pozycja])
        top_blocks[pozycja] = klocek

    # posortowanie, tak żeby opisywał klocki w kolejności od 1 do N
    polaczone_sorted = sorted(zip(klocki, state))
    state = [i for _, i in polaczone_sorted]

    return BlocksState(state)


print(generate_state(5).state)