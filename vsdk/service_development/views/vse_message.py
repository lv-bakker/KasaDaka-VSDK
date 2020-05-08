from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect

from ..models import *

def message_presentation_get_redirect_url(message_presentation_element,session):
    if not message_presentation_element.final_element:
        return message_presentation_element.redirect.get_absolute_url(session)
    else:
        return None



def message_presentation_generate_context(message_presentation_element,session):
    language = session.language
    message_voice_fragment_url = message_presentation_element.get_voice_fragment_url(language)
    redirect_url = message_presentation_get_redirect_url(message_presentation_element,session)
    context = {'message_voice_fragment_url':message_voice_fragment_url,
            'redirect_url':redirect_url}
    return context


def message_presentation(request, element_id, session_id):
    message_presentation_element = get_object_or_404(MessagePresentation, pk=element_id)
    session = get_object_or_404(CallSession, pk=session_id)
    session.record_step(message_presentation_element)
    context = message_presentation_generate_context(message_presentation_element, session)

    if element_id == '47':
        if request.method == "POST":
            print("POST to message presentation")
            phone = request.POST['submit_phone']
            print("Received Phone: " + str(phone))
            session.target_phonenr = phone # store in db
            session.record_step()
            return redirect(request.POST['redirect'])
        context['phone_nr'] = 'test ' + str(session.target_phonenr)

    # /vxml/message/39/92
    # if element_id == '39':
        # context['forward_call'] = 1 # phone_nr

    return render(request, 'message_presentation.xml', context, content_type='text/xml')
