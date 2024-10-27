$(document).ready(function(){

    // Toggle like/unlike button
    $('.list-group-item').on('click', '.like-btn', async function(event) {

        event.preventDefault()

        const $msgId = ($(this).attr('data-msg-id'))

        try {
            const res = await axios.post(`/users/add_like/${$msgId}`)
            
            if(res.data.liked){
                $(this).removeClass('btn-secondary').addClass('btn-primary')
            }
            else{
                $(this).removeClass('btn-primary').addClass('btn-secondary')
            }
        }
        catch (err){
            console.error("Error: ", err)
        }

    })


    /* Modal functionality */

    // Open the modal when the "open-warbler" button is clicked
    $('#open-modal').on('click', function(){
        $('#warbler-modal').css('display', 'block')
    })

    // Close the modal when the "close" button is clicked
    $('#close-modal').on('click', function(){
        $('#warbler-modal').css('display', 'none')
    })


})
