# -*- coding: utf-8 -*-

'''
Implementation of 'TnT - A Statisical Part of Speech Tagger'
'''

from math import log

import frequency

class TnT(object):

    def __init__(self, N=1000):
        self.N = N
        self.l1 = 0.0
        self.l2 = 0.0
        self.l3 = 0.0
        self.status = {'BOS', 'EOS'}
        self.wd = frequency.AddOneProb()
        self.uni = frequency.AddOneProb()
        self.bi = frequency.AddOneProb()
        self.tri = frequency.AddOneProb()
        self.eos = frequency.AddOneProb()
        self.trans = {}

    def _safe_div(self, v1, v2):
        if v2 == 0:
            return -1
        return float(v1) / float(v2)

    def train(self, data):
        now = ['BOS', 'BOS']
        for sentence in data:
            for word, tag in sentence:
                now.append(tag)
                self.status.add(tag)
                self.wd.add((tag, word), 1)
                self.uni.add(tag, 1)
                self.bi.add(tuple(now[1:]), 1)
                self.tri.add(tuple(now), 1)
                now.pop(0)
            self.eos.add(now[-1], 1)
        tl1 = 0.0
        tl2 = 0.0
        tl3 = 0.0
        for now in self.tri.samples():
            c1 = self._safe_div(self.tri.get(now)[1]-1,
                                self.bi.get(now[:2])[1]-1)
            c2 = self._safe_div(self.bi.get(now[1:])[1]-1,
                                self.uni.get(now[1])[1]-1)
            c3 = self._safe_div(self.uni.get(now[2])[1]-1,
                                self.uni.getsum()-1)
            if c1 > c2 and c1 > c3:
                tl1 += self.tri.get(now)[1]
            elif c2 > c1 and c2 > c3:
                tl2 += self.tri.get(now)[1]
            elif c3 > c1 and c3 > c2:
                tl3 += self.tri.get(now)[1]
            elif c1 == c2 and c1 > c3:
                tl1 += self.tri.get(now)[1]/2.0
                tl2 += self.tri.get(now)[1]/2.0
            elif c2 == c3 and c2 > c1:
                tl2 += self.tri.get(now)[1]/2.0
                tl3 += self.tri.get(now)[1]/2.0
            elif c1 == c3 and c1 > c2:
                tl3 += self.tri.get(now)[1]/2.0
                tl1 += self.tri.get(now)[1]/2.0
        self.l1 = self._safe_div(tl1, tl1+tl2+tl3)
        self.l2 = self._safe_div(tl2, tl1+tl2+tl3)
        self.l3 = self._safe_div(tl3, tl1+tl2+tl3)
        for s1 in self.status:
            for s2 in self.status:
                for s3 in self.status:
                    uni = self.l3*self.uni.freq(s3)
                    bi = self.l2*self.bi.freq((s2, s3))
                    tri = self.l1*self.tri.freq((s1, s2, s3))
                    self.trans[(s1, s2, s3)] = log(uni+bi+tri)

    def tag(self, data):
        now = [(('BOS', 'BOS'), 0.0, [])]
        for w in data:
            stage = {}
            for s in self.status:
                wd = log(self.wd.get((s, w))[1])
                for pre in now:
                    p = pre[1]+wd+self.trans[(pre[0][0], pre[0][1], s)]
                    if (pre[0][1], s) not in stage or p > stage[(pre[0][1], s)][0]:
                        stage[(pre[0][1], s)] = (p, pre[2]+[s])
            stage = map(lambda x: (x[0], x[1][0], x[1][1]), stage.items())
            now = sorted(stage, key=lambda x:-x[1])[:self.N]
            print len(now)
        for cnt, item in enumerate(now):
            now[cnt] = (item[0], item[1]+log(self.eos.freq(item[0][1])), item[2])
        now = sorted(stage, key=lambda x:-x[1])[:self.N]
        return zip(data, now[0][2])
