from state import BlocksState

def verify_sequence(state, target_state, sequence, third_move):
    def invalid_move(movenumber, move, message):
        print(f"Move {move} (move number:{movenumber + 1}) invalid.")
        print(message)
        return False

    current_state = state

    for movenumber, move in enumerate(sequence):
        block, target = move
        free_blocks = current_state.get_free_blocks()

        # Check if the block is free
        if block not in free_blocks:
            return invalid_move(movenumber, move, "block is not free.")

        # Move on itself?
        if target == block:
            return invalid_move(movenumber, move, "tried to move block onto itself.")

        support = current_state.state[block - 1]

        if support == 0:  # Block is on the table
            if target == 0:
                return invalid_move(movenumber, move, "tried to move block from table to table.")

            if target not in free_blocks:
                return invalid_move(movenumber, move, f"{target} is not free.")

        else:   # Block is on another block
            if not third_move:  # 2 moves variant
                if target != 0:
                    return invalid_move(
                        movenumber,
                        move,
                        "tried to move block from a block to another block.",
                    )
            else:  # 3 moves variant
                if target not in free_blocks and target != 0:
                    return invalid_move(movenumber, move, "target is not free.")

        # Apply the move
        new_state_list = list(current_state.state)
        new_state_list[block - 1] = target
        current_state = BlocksState(new_state_list)

    if current_state != target_state:
        print(f"Sequence does not lead to the target state."
              f" Final state: {current_state.state}, Target state: {target_state.state}")
        return False

    print("Sequence is valid and leads to the target state.")
    return True