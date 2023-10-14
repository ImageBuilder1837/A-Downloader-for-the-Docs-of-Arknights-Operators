import os
import re
import requests
from lxml import etree


# ===============常量定义===============


elites = ["Pith", "Sharp", "Stormeye", "Touch", "郁金香"]
ptn_mark = re.compile(r'<mark.*?>(.*?)</mark>')
ptn_sup = re.compile(r'<sup.*?>.*?</sup>')


# ===============基石函数===============


def encode(lis):
    '''将列表中的字符串末尾加上编号'''

    cop, count = [], {}
    for i in lis:
        if i not in count:
            cop.append(i + "_0")
            count[i] = 1
        else:
            cop.append(i + f"_{count[i]}")
            count[i] += 1
    return cop


def decode(string):
    '''去除字符串末尾编号'''
    return '_'.join(string.split('_')[:-1])


def filtering(lis):
    '''去除列表中的空项'''
    return list(filter(bool, map(str.strip, lis)))


def fetch_ones_text(name):
    '''从网上下载某个干员主页html源码并判断是否正确'''

    url = f"http://prts.wiki/w/{name}"
    resp = requests.get(url)
    text = resp.text
    html = etree.HTML(text)
    if html.xpath("//title/text()")[0] != f"{name} - PRTS - 玩家共同构筑的明日方舟中文Wiki":
        print(f"{url} is not accessible!")
        assert False
    return text


# ===============底层函数===============


def get_operator_list():
    '''获取干员列表'''

    Lancet_2 = fetch_ones_text("Lancet-2")
    html = etree.HTML(Lancet_2)
    operators = html.xpath("//table/tbody/tr/td/div/ul/li/span/span/a/text()")
    return operators + elites


def get_file(text):
    '''从html源码中提取干员档案'''

    while ans := re.search(ptn_mark, text):
        text = text[:ans.start()] + ans.group(1) + text[ans.end():]
    while re.search(ptn_sup, text):
        text = re.sub(ptn_sup, '', text)

    html = etree.HTML(text)
    titles = filtering(html.xpath("//table[@class='wikitable mw-collapsible mw-collapsed logo']"
                                  "/tbody/tr/th[@style='text-align:left;color:white;background:#424242;']"
                                  "/div/p/text()"))
    paras = filtering(html.xpath("//table[@class='wikitable mw-collapsible mw-collapsed logo']"
                                 "/tbody/tr/td/div/p/text()"))

    titles_e, paras_e = encode(titles), encode(paras)
    dic, st = {}, 0
    for title in titles_e:
        dic[title] = text.find(decode(title), st)
        st = dic[title] + len(title) - len(title.split('_')[-1])
    st = 0
    for para in paras_e:
        dic[para] = text.find(decode(para), st)
        st = dic[para] + len(para) - len(title.split('_')[-1])

    all_conts = titles_e + paras_e
    all_conts.sort(key=lambda x: dic[x])
    file = '\n\n'.join(map(decode, all_conts))
    return file


def get_voices(text):
    '''从html源码中提取干员语音记录'''

    html = etree.HTML(text)
    voices = html.xpath("//div/div/div[@data-kind-name='中文']/text()")
    titles = html.xpath("//div/div/@data-title")

    if len(voices) != len(titles):
        print("voices' amount is wrong!")
        assert False
    record = ""
    for title, voice in zip(titles, voices):
        record += f"{title}\n\n{voice}\n\n"
    return record


def get_modules(text):
    '''从html源码中提取干员模组文案'''

    html = etree.HTML(text)
    modules = html.xpath("//h3/span[@class='mw-headline']/text()")
    if not modules:
        return

    module_text = ""
    for i in range(1, len(modules)):
        paras = filtering(html.xpath(
            f"//div/div/div/div/div/div/div/div[@id='mw-customcollapsible-module-{i+1}']/div/text()"))
        module_text += '\n\n'.join([modules[i] + f"（第{'一二三四五六七八九'[i-1]}模组）", *paras]) + '\n\n'
    return module_text.strip()


# ===============终端函数===============


def get_one(name, type_):
    '''下载并保存某干员（档案、模组文案、语音记录）'''

    print(f"downloading {name}'s html...")
    text = fetch_ones_text(name)

    if "file" in type_:
        print(f"getting {name}'s file...", end=' ')
        file = get_file(text)

        if not os.path.exists("干员档案"):
            os.mkdir("干员档案")
        with open(f"干员档案\\明日方舟干员档案（{name}）.txt", 'w', encoding='utf-8') as f:
            f.write(file)
        print("done!")

    if "voices" in type_:
        print(f"getting {name}'s voices...", end=' ')
        record = get_voices(text)

        if not os.path.exists("干员语音"):
            os.mkdir("干员语音")
        with open(f"干员语音\\明日方舟干员语音（{name}）.txt", 'w', encoding='utf-8') as f:
            f.write(record)
        print("done!")

    if "modules" in type_:
        print(f"getting {name}'s modules...", end=' ')
        modules = get_modules(text)
        if not os.path.exists("干员模组"):
            os.mkdir("干员模组")

        if modules:
            with open(f"干员模组\\明日方舟干员模组（{name}）.txt", 'w', encoding='utf-8') as f:
                f.write(modules)
            print("done!")
        else:
            print("no modules!")


def get_one_combined(name):
    '''下载并合并保存某干员（档案、语音记录、模组文案）'''

    print(f"downloading {name}'s html...")
    text = fetch_ones_text(name)

    print(f"combining {name}'s doc...", end=' ')
    file = get_file(text)
    record = get_voices(text)
    modules = get_modules(text)
    doc = f"一、干员档案\n\n{file}\n\n二、语音记录\n\n{record}三、模组文案\n\n{modules if modules else '该干员暂无模组'}"

    if not os.path.exists("干员资料"):
        os.mkdir("干员资料")
    with open(f"干员资料\\明日方舟干员资料（{name}）.txt", 'w', encoding='utf-8') as f:
        f.write(doc)
    print("done!")


def get_all(type_):
    '''下载并保存所有干员（档案、模组文案、语音记录）'''

    print("getting operator list...", end=' ')
    Lancet_2 = fetch_ones_text("Lancet-2")
    operators = get_operator_list(Lancet_2)
    print("done!")

    for operator in operators:
        get_one(operator, type_)


def get_all_combined():
    '''下载并合并保存所有干员（档案、语音记录、模组文案）'''

    print("getting operator list...", end=' ')
    operators = get_operator_list()
    print("done!")

    for operator in operators:
        get_one_combined(operator)


def main():
    ans = input("please input operators' name: ").strip()
    if ans.lower() == "all":
        get_all_combined()
    else:
        op_lis = ans.split()
        for op in op_lis:
            get_one_combined(op)


if __name__ == "__main__":
    main()
