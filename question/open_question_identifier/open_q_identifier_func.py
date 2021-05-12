#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 10 13:31:33 2021

@author: shintanitaketo
"""
 # 重複特殊文字の削除用
import neologdn

# 文区切り用
import functools
from ja_sentence_segmenter.common.pipeline import make_pipeline
from ja_sentence_segmenter.concatenate.simple_concatenator import concatenate_matching
from ja_sentence_segmenter.normalize.neologd_normalizer import normalize
from ja_sentence_segmenter.split.simple_splitter import split_newline, split_punctuation

# 正規表現用
import re

def question_sentence_splitter(question: str) -> list:
    """
    
    入力された質問を、正規化し、文章単位に分ける関数
    
    """

    # questionの正規化
    question = neologdn.normalize(question, repeat=2)
    
    # 文区切りの事前準備
    split_punc2 = functools.partial(split_punctuation, punctuations=r"。!?")
    concat_tail_no = functools.partial(concatenate_matching, 
                                       former_matching_rule=r"^(?P<result>.+)(の)$", 
                                       remove_former_matched=False)
    segmenter = make_pipeline(normalize, split_newline, concat_tail_no, split_punc2)
    
    # 文が区切られた質問のリストを返す
    return list(segmenter(question))



def question_extractor(questions: list) -> list:
    """
    
    リストに格納された、それぞれの質問文章が疑問文なのか、を判定し、疑問文のみを返す関数
    
    条件ロジックの説明
    ・「5W1Hが入っていない」のであれば、それは「文末、疑問助詞(疑問文)」or 「コメント(not疑問文)」
    ・「5W1Hが入っている」であれば、それは「疑問詞(疑問文)」or「副詞(not疑問文)」or 「疑問詞 and 副詞(どちらかわからない)」
    
    """
    
    regex_wh  = r'(いつ|どこ|どこで|誰|誰が|だれが|だれ|何|何を|なに|なにを|なんでしょうか|なんですか|なぜ|どう|どの|どうすれば|いかにして|どんな)'
    regex_eos = r'(か|って|かい|の|って|け|ね)[?。.]*$' 
    regex_ad = r"(いつも|誰かしら|だれかしら|なにかしら|何かしら|何か|何と|なにと|なにか|どこかしら|どこか)" 

    
    
    # 5W1H判定の判定
    question_list = []
    for q in questions:
        
        ##### 5W1H入ってない #####
        if re.search(regex_wh, q) is None:
            
            # かつ、文末に「~か？」がついているパターン -> 疑問文
            if re.search(regex_eos, q) is not None:
                print("5W1H入ってない、かつ、文末に「~か？」がついている -> 疑問文")
                question_list.append(q)
            # 文末に「~か？」がついていないパターン -> not疑問文
            else:
                print("5W1H入ってない、かつ、文末に「~か？」がついているパターン -> not疑問文")
                continue
        
        ##### 5W1H入っている #####
        elif re.search(regex_wh, q) is not None:
            
            # かつ、副詞が入っていない
            if re.search(regex_ad, q) is None:
                
                # かつ、文末に「~か」がない - > not疑問文
                if re.search(regex_eos, q) is None:
                    print("5W1H入っている、副詞が入っていない、かつ、文末に「~か」がない - > not疑問文")
                    continue
                # 文末に「~か」がある - > 疑問文
                else:
                    print("5W1H入っている、副詞が入っていない、かつ、文末に「~か」がある - > 疑問文")
                    question_list.append(q)
                
            # かつ、副詞が入っている
            elif re.search(regex_ad, q) is not None:
                
                # かつ、文末に「~か」がない - > not疑問文
                if re.search(regex_eos, q) is None:
                    print("5W1H入っている、副詞が入っている、かつ、文末に「~か」がない - > not疑問文")
                    continue
                #かつ、文末に「~か」がある -> 疑問文
                else:
                    print("5W1H入っている、副詞が入っている、かつ、文末に「~か」がある - > 疑問文")
                    question_list.append(q)
        
        # 紛れもない、ただのコメント
        else:
            print("紛れもない、ただのコメント")
            continue
            
    return question_list

  
def open_question_identifier(questions: list):
    """
    
    リストに格納された、一番最後の質問文章が「OpenQ」なのかを判定し、True or Falseを返す関数
    入力値は、質問文章に絞られているので、文末「~か」の表現かどうか、は気にしなくて良い
    
    """
    regex_wh  = r'(いつ|どこ|どこで|誰|誰が|だれが|だれ|何|何を|なに|なにを|なんですか|なんでしょうか|なぜ|どう|どの|どう|いかにして|どんな)'
    regex_eos = r'(か|って|かい|の|って|け|ね)[?。.]*$' 
    regex_ad = r"(いつも|誰かしら|だれかしら|なにかしら|何かしら|何か|何と|なにと|なにか|どこかしら|どこか)" 
    
    
    # 一番最後の質問を抜き出す
    q = questions[-1]
    q = q.split("、")[-1]
    
    # 5W1Hが入っていない -> not openQ
    if re.search(regex_wh, q) is None:
        return "not_open"
    
    # 5W1Hが入っている
    elif re.search(regex_wh, q) is not None:
        #かつ、副詞が含まれている -> not openQ
        if re.search(regex_ad, q) is not None:
            return "not_open"
        
        # かつ、副詞が含まれていない -> openQ
        else:
            return "open"