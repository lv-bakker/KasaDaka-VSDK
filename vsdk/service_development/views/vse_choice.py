from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect

from ..models import *

# for scanning WAV files
import requests
import re

def choice_options_resolve_redirect_urls(choice_options, session):
    choice_options_redirection_urls = []
    for choice_option in choice_options:
        redirect_url = choice_option.redirect.get_absolute_url(session)
        choice_options_redirection_urls.append(redirect_url)
    return choice_options_redirection_urls

def choice_options_resolve_voice_labels(choice_options, language):
    """
    Returns a list of voice labels belonging to the provided list of choice_options.
    """
    choice_options_voice_labels = []
    for choice_option in choice_options:
        choice_options_voice_labels.append(choice_option.get_voice_fragment_url(language))
    return choice_options_voice_labels

def choice_generate_context(choice_element, session):
    """
    Returns a dict that can be used to generate the choice VXML template
    choice = this Choice element object
    choice_voice_label = the resolved Voice Label URL for this Choice element
    choice_options = iterable of ChoiceOption object belonging to this Choice element
    choice_options_voice_labels = list of resolved Voice Label URL's referencing to the choice_options in the same position
    choice_options_redirect_urls = list of resolved redirection URL's referencing to the choice_options in the same position
        """
    choice_options =  choice_element.choice_options.all()
    language = session.language
    context = {'choice':choice_element,
                'choice_voice_label':choice_element.get_voice_fragment_url(language),
                'choice_options': choice_options,
                'choice_options_voice_labels':choice_options_resolve_voice_labels(choice_options, language),
                    'choice_options_redirect_urls': choice_options_resolve_redirect_urls(choice_options,session),
                    'language': language,
                    }
    return context

def choice(request, element_id, session_id):
    choice_element = get_object_or_404(Choice, pk=element_id)
    session = get_object_or_404(CallSession, pk=session_id)
    session.record_step(choice_element)
    context = choice_generate_context(choice_element, session)

    seed_search_choices = ['55', '58', '61', '64']  # 13
    if element_id in seed_search_choices:

        seedtype = "rice"
        bags_of_seedtype_wav = "bags_of_rice.wav"
        if element_id == '55':
            seedtype = "arachide"
            bags_of_seedtype_wav = "bags_of_arachide.wav"
        elif element_id == '58':
            seedtype = "fonio"
            bags_of_seedtype_wav = "bags_of_fonio.wav"
        elif element_id == '61':
            seedtype = "mais"
            bags_of_seedtype_wav = "bags_of_mais.wav"

        # 1. fetch all the stored advertisements (WAV files)
        url = "http://ict4d.saadittoh.com/group12/django/uploads/"
        refs = re.findall(r'(?<=<a href=")[^"]*', requests.get(url).text)
        wavs = [idx for idx in refs if idx.startswith("bags")]

        new_voice_labels = []
        phones = []

        # 2. find the advertisements related to this search
        cur_lang = str(session._language.code)
        print("----- WAV storage: -----")
        for wav in wavs:
            wav_data = wav.split('_')
            # 0 bags 1 lang 2 seedtype 3 phonenr 4 datetime
            if cur_lang == wav_data[1] and wav_data[2] == seedtype: # request is searching for this
                print(wav, wav_data[2], wav_data[3])
                new_voice_labels.append(url + wav)
                phones.append(wav_data[3])

        # 3. update the context to match the request (if there are stored ads)
        if len(new_voice_labels) > 0:
            context['mali_seeds_choose_phone'] = 1
            context['bags_of_seedtype'] = 'http://ict4d.saadittoh.com/group12/django/' + cur_lang + '_' + bags_of_seedtype_wav
            context['phone_nrs'] = phones
            context['post_url'] = (context['choice_options_redirect_urls'])[0] #'/vxml/message/12/39'

            # choice_options_voice_labels: ['/uploads/1_nl.wav', '/uploads/2_nl.wav']
            # choice_options: <InheritanceQuerySet [<ChoiceOption: (test choice): opt1>, <ChoiceOption: (test choice): opt2>]>
            # choice_options_redirect_urls: ['/vxml/message/12/34', '/vxml/message/12/34']
            context['choice_options_voice_labels'] = new_voice_labels
            context['choice_options'] = range(1, len(new_voice_labels)+1)

    return render(request, 'choice.xml', context, content_type='text/xml')
