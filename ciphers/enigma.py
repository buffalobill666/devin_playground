"""Enigma I — симулятор исторической машины (Wehrmacht, 3 ротора).

Проводки роторов I–V и рефлекторов B/C — реальные таблицы.
Механика: коммутатор -> роторы справа налево -> рефлектор ->
обратно. Шаги — с двойным ходом среднего ротора (double-stepping),
как у физических собачек и зубчатки.

Тест-вектор: роторы I II III, рефлектор B, rings AAA, pos AAA,
без коммутатора: AAAAA -> BDZGO (исторический).
"""

ALPH = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

ROTORS = {
    'I':   ('EKMFLGDQVZNTOWYHXUSPAIBRCJ', 'Q'),
    'II':  ('AJDKSIRUXBLHWTMCQGZNPYFVOE', 'E'),
    'III': ('BDFHJLCPRTXVZNYEIWGAKMUSQO', 'V'),
    'IV':  ('ESOVPZJAYQUIRHXLNFTGKDCMWB', 'J'),
    'V':   ('VZBRGITYUPSDNHLXAWMJQOFECK', 'Z'),
}

REFLECTORS = {
    'B': 'YRUHQSLDPXNGOKMIEBFZCWVJAT',
    'C': 'FVPJIAOYEDRZXWGCTKUQSBNMHL',
}


class Rotor:
    def __init__(self, name, ring=0, pos=0):
        wiring, notch = ROTORS[name]
        self.fwd = [ALPH.index(c) for c in wiring]
        self.rev = [0] * 26
        for i, v in enumerate(self.fwd):
            self.rev[v] = i
        self.notch_i = ALPH.index(notch)
        self.ring = ring
        self.pos = pos

    def at_notch(self):
        return self.pos == self.notch_i

    def step(self):
        self.pos = (self.pos + 1) % 26

    def forward(self, i):
        o = self.fwd[(i + self.pos - self.ring) % 26]
        return (o - self.pos + self.ring) % 26

    def backward(self, i):
        o = self.rev[(i + self.pos - self.ring) % 26]
        return (o - self.pos + self.ring) % 26


class Enigma:
    """rotors — имена слева направо, как в машине; rings/pos — AAA-начало."""

    def __init__(self, rotors, reflector='B', rings=(0, 0, 0),
                 pos=(0, 0, 0), plugs=''):
        self.left, self.middle, self.right = [
            Rotor(n, r, p) for n, r, p in zip(rotors, rings, pos)]
        self.refl = [ALPH.index(c) for c in REFLECTORS[reflector]]
        self.plug = list(range(26))
        for a, b in zip(plugs[0::2], plugs[1::2]):
            i, j = ALPH.index(a), ALPH.index(b)
            self.plug[i], self.plug[j] = j, i

    def window(self):
        return ''.join(ALPH[r.pos]
                       for r in (self.left, self.middle, self.right))

    def _step(self):
        # двойной ход: средний на насечке шагает сам + двигает левый
        if self.middle.at_notch():
            self.middle.step()
            self.left.step()
        if self.right.at_notch():
            self.middle.step()
        self.right.step()

    def enc_char(self, c):
        self._step()
        i = self.plug[ALPH.index(c)]
        for r in (self.right, self.middle, self.left):
            i = r.forward(i)
        i = self.refl[i]
        for r in (self.left, self.middle, self.right):
            i = r.backward(i)
        return ALPH[self.plug[i]]

    def enc(self, text):
        return ''.join(self.enc_char(c) for c in text.upper() if c in ALPH)


if __name__ == '__main__':
    m = Enigma(('I', 'II', 'III'))
    ct = m.enc('AAAAA')
    print('vector AAAAA ->', ct, '| expected BDZGO |', 'OK' if ct == 'BDZGO' else 'FAIL')

    m = Enigma(('I', 'II', 'III'), plugs='BQCRDIJKNMPOSUXW')
    ct = m.enc('HELLOWORLD')
    print('with plugboard HELLOWORLD ->', ct)
    m2 = Enigma(('I', 'II', 'III'), plugs='BQCRDIJKNMPOSUXW')
    print('roundtrip decrypt ->', m2.enc(ct))

    print('\ndouble-stepping demo (start pos ADV):')
    m = Enigma(('I', 'II', 'III'), pos=(0, 3, 21))
    for _ in range(5):
        m.enc_char('X')
        print(' ', m.window())
