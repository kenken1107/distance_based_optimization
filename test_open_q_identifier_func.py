#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 10 13:08:17 2021

@author: shintanitaketo
"""
import pytest
import open_q_identifier_func as oqf

@pytest.mark.parametrize(
    "p1, result, result_final", [
        ("「複数の示唆を、論点で、一つに絞り出す」という感覚がまだ理解できません。この先の章で、解説がありますでしょうか？",list, "not_open"),
        ("これは、なんですか？ラーメンですか？",list, "not_open"),
        ("これはなんですか？", list, "open"),
        ("論点とは、なんでしょうか？ご教示いただけると幸いでございます。",list, "open"),
        ("どこかに何かしら、ありますか？",list, "not_open"),
        ("これはなんですか",list, "open"),
        ("これはなんですか?ラーメンですか？", list, "not_open")
        ]
    )

class TestAll(object):
    def test_splitter_type(self, p1, result, result_final):
        assert type(oqf.question_sentence_splitter(p1)) is result
    
    def test_splitter_lengths(self, p1, result, result_final):
        assert len(oqf.question_sentence_splitter(p1)) >= 1
    
    def test_extractor__type(self, p1, result, result_final):
        sentences = oqf.question_sentence_splitter(p1)
        questions = oqf.question_extractor(sentences)
        assert (type(questions) is list) or (type(questions) is None)
    
    def test_result(self, p1, result, result_final):
        sentences = oqf.question_sentence_splitter(p1)
        questions = oqf.question_extractor(sentences)
        q_type    = oqf.open_question_identifier(questions)
        assert q_type == result_final
