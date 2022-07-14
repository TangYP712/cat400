var skins = ["ffdbb4","edb98a","fd9841","d08b5b","ae5d29","614335"];
var eyes = ["default","dizzy","eyeroll","happy","close","hearts","side","wink","squint","surprised","winkwacky","cry"];
var eyebrows = ["default","default2","raised","sad","sad2","unibrow","updown","updown2","angry","angry2"];
var mouths = ["default","twinkle","tongue","smile","serious","scream","sad","grimace","eating","disbelief","concerned","vomit"];
var hairstyles = ["bold","longhair","longhairbob","hairbun","longhaircurly","longhaircurvy","longhairdread","nottoolong","miawallace","longhairstraight","longhairstraight2","shorthairdreads","shorthairdreads2","shorthairfrizzle","shorthairshaggy","shorthaircurly","shorthairflat","shorthairround","shorthairwaved","shorthairsides"];
var haircolors = ["bb7748_9a4f2b_6f2912","404040_262626_101010","c79d63_ab733e_844713","e1c68e_d0a964_b88339","906253_663d32_3b1d16","f8afaf_f48a8a_ed5e5e","f1e6cf_e9d8b6_dec393","d75324_c13215_a31608","59a0ff_3777ff_194bff"];
// var facialhairs = ["none","magnum","fancy","magestic","light"];
var clothesmenu = ["vneck","sweater","hoodie","overall","blazer"];
// var fabriccolors = ["545454","65c9ff","5199e4","25557c","e6e6e6","929598","a7ffc4","ffdeb5","ffafb9","ffffb1","ff5c5c","e3adff"];
// var backgroundcolors = ["ffffff","f5f6eb","e5fde2","d5effd","d1d0fc","f7d0fc","d0d0d0"];

var foundationcolors = ["D29D68","E9BD9A","DBAB80","DBB685","EBCFBB","D49962","F7D4C0","DABB8F","D1A969","FAC794","DCA588","ECAE7A","CEAF8C"];
var foundation_name = ["BB_SLWW_Natural","EL_DWSIPM_Cool Bone","BB_SLWW_Warmsand","BB_SWPF_Natural","BB_SLWW_Porcelain","CLINIQUE_EBMF_Chestnut","CLINIQUE_EBRHRMF_Fresh Beige","BB_SWPF_Beige","EL_DWSIPM_Rattan","EL_DWSIPMPF_Wheat","EL_DWSLWM_Ecru","FB_PFSMLF_200","LC_TIUWF_01"];

var lipscolors = ["8D4148","C07869","FFBDBA","B75566","78383A","AA5F5F","883D4D","FC382C","A5242F","942F36","2D0509","BC7980","B56D58","D73140","B74336"];
var lipscolors_name = ["BB_LLC_Downtown Plum","BB_LLC_Neutral Rose","BB_ELT_Bare Pink","BB_CLL_Smoothie Move","BB_CLL_Haute Cocoa","CLINIQUE_CSMLCB_Whole Lotta Honey","CLINIQUE_PLCP_Bare Pop","CLINIQUE_PLCP_Melon Pop","CLINIQUE_PLCP_Cherry Pop","EL_PCWMLCLWMB_Soft Hearted","EL_PCWMLCLWMB_Bar Noir","FB_GBULL_Fussy","FB_GBULL_Fenty Glow","LC_LARDML_505","LC_LARDML_196"]

var current_skincolor = "edb98a";
var current_hairstyle = "longhair";
var current_haircolor = "bb7748_9a4f2b_6f2912";
var current_fabriccolors = "545454";
var current_backgroundcolors = "ffffff";

var current_foundationcolor = "";

var current_lipscolors = "FC0023";

$(document).ready(function() {
    $("#options_form").hide();

    $("body").on("click","#menu_list button",function() {

        var idx = $(this).attr("id");

            var selected = $(this).html();

            $("#options_title").html("Select "+selected);
            $("#options_div").html("");

            var html = "";

            switch (idx) {
                case "skincolor":
                    $("#options_form").hide();
                    for (var i=0;i<skins.length; i++) {
                        skin = skins[i];
                        html += "<div class='skins' id='s_"+skin+"' style='background-color:#"+skin+";'></div>";
                    }
                    break;
                case "eyes":
                    $("#options_form").hide();
                    for (i=0;i<eyes.length; i++) {
                        eye = eyes[i];
                        html += "<div class='eyes' id='e_"+eye+"' style='background-color:#"+current_skincolor+";background-position:"+(i*-53)+"px 0px;'></div>";
                    }
                    break;
                case "eyebrows":
                    $("#options_form").hide();
                    for (i=0;i<eyebrows.length; i++) {
                        eyebrow = eyebrows[i];
                        html += "<div class='eyebrows' id='eb_"+eyebrow+"' style='background-color:#"+current_skincolor+";background-position:"+(i*-53)+"px -53px;'></div>";
                    }
                    break;
                case "mouths":
                    $("#options_form").hide();
                    for (i=0;i<mouths.length; i++) {
                        mouth = mouths[i];
                        html += "<div class='mouths' id='m_"+mouth+"' style='background-color:#"+current_skincolor+";background-position:"+(i*-53)+"px -106px;'></div>";
                    }
                    break;
                case "hairstyles":
                    $("#options_form").hide();
                    for (i=0;i<hairstyles.length; i++) {
                        hairstyle = hairstyles[i];
                        html += "<div class='hairstyles' id='h_"+hairstyle+"' style='background-color:#ffffff;background-position:"+(i*-53)+"px -159px;'></div>";
                    }
                    break;
                case "haircolors":
                    $("#options_form").hide();
                    for (i=0;i<haircolors.length; i++) {
                        haircolor = haircolors[i];
                        haircolor_front = haircolor.split("_");
                        html += "<div class='haircolors' id='hc_"+haircolor+"' style='background-color:#"+haircolor_front[0]+";'></div>";
                    }
                    break;
                case "facialhairs":
                    $("#options_form").hide();
                    for (i=0;i<facialhairs.length; i++) {
                        facialhair = facialhairs[i];
                        haircolor_front = facialhair.split("_");
                        html += "<div class='facialhairs' id='f_"+facialhair+"' style='background-color:#ffffff;background-position:"+(i*-53)+"px -212px;'></div>";
                    }
                    break;
                case "clothesmenu":
                    $("#options_form").hide();
                    for (var i=0;i<clothesmenu.length; i++) {
                        clothe = clothesmenu[i];
                        html += "<div class='clothesmenu' id='c_"+clothe+"' style='background-color:#ffffff;background-position:"+(i*-53)+"px -265px;'></div>";
                    }
                    break;
                case "fabriccolors":
                    $("#options_form").hide();
                    for (var i=0;i<fabriccolors.length; i++) {
                        fabriccolor = fabriccolors[i];
                        html += "<div class='fabriccolors' id='f_"+fabriccolor+"' style='background-color:#"+fabriccolor+";'></div>";
                    }
                    break;
                case "backgroundcolors":
                    $("#options_form").hide();
                    for (var i=0;i<backgroundcolors.length; i++) {
                        backgroundcolor = backgroundcolors[i];
                        html += "<div class='backgroundcolors' id='g_"+backgroundcolor+"' style='background-color:#"+backgroundcolor+";'></div>";
                    }
                    break;
                case "foundationcolors":
                    $("#options_form").show();
                    for (var i=0;i<foundationcolors.length; i++) {
                        foundation = foundationcolors[i];
                        fname = foundation_name[i];
                        html += "<div class='foundationcolors' id='f_"+foundation+"' style='background-color:#"+foundation+"' title='"+fname+"';'></div>";
                    }
                    break;
                case "lipscolors":
                    $("#options_form").show();
                    for (var i=0;i<lipscolors.length; i++) {
                        lips = lipscolors[i];
                        colorname = lipscolors_name[i];
                        html += "<div class='lipscolors' id='l_"+lips+"' style='background-color:#"+lips+"' title='"+colorname+"';></div>";
                    }
                    break;
            }
            $("#options_div").html(html);
            $("#menu_lines").click();
        
    });

   
    $("body").on("click",".skins",function() {
        var id = $(this).attr("id");
        id = id.substr(2);
        current_skincolor = id;
        $("#skin_color #body").attr("fill","#"+id);
        const myObj = {skin: id};
        const myJSON = JSON.stringify(myObj);
    });

    $("body").on("click",".foundationcolors",function() {
        var id = $(this).attr("id");
        id = id.substr(2);
        current_foundationcolor = id;
        var fname = $(this).attr("title");
        $("#foundation_color #foundation #body2").attr("fill","#"+id);
        $("#foundation_color #foundation").show()
        $("#foundation_color #foundation #body2").attr("fill-opacity",0.45);

        $("input[name=product_name]").val(fname);

        const myObj = {foundation: id};
        const myJSON = JSON.stringify(myObj);
    });

    $("body").on("click",".lipscolors",function() {
        var id = $(this).attr("id");
        id = id.substr(2);
        current_lipscolors = id;
        var lname = $(this).attr("title");
        $("#lips #lips #outerlips").attr("fill","#"+id);

        $("input[name=product_name]").val(lname);

        const myObj = {lips: id};
        const myJSON = JSON.stringify(myObj);
    });




    $("body").on("click",".eyes",function() {
        var id = $(this).attr("id");
        id = id.substr(2);
        $("#eye g").hide();
        var eyes_s = $("#eye #e_"+id).show();
    });

    $("body").delegate(".eyebrows","click",function() {
        var id = $(this).attr("id");
        id = id.substr(3);
        $("#eyebrow g").hide();
        $("#eyebrow #eb_"+id).show();
    });

    $("body").delegate(".mouths","click",function() {
        var id = $(this).attr("id");
        id = id.substr(2);
        $("#mouth g").hide();
        $("#mouth #m_"+id).show();
    });

    $("body").delegate(".hairstyles","click",function() {
        var id = $(this).attr("id");
        id = id.substr(2);
        current_hairstyle = id;
        $("#hair_front g").hide();
        $("#hair_back g").hide();
        $("#hair_front .h_"+id).show();
        $("#hair_back .h_"+id).show();
        var color = current_haircolor;
        color = color.split("_");
        $("#hair_front .h_"+current_hairstyle+" .tinted").attr("fill","#"+color[0]);
        $("#hair_back .h_"+current_hairstyle+" .tinted").attr("fill","#"+color[1]);
        $("#facialhair g .tinted").attr("fill","#"+color[2]);
    });

    $("body").delegate(".haircolors","click",function() {
        var id = $(this).attr("id");
        id = id.substr(3);
        current_haircolor = id;
        id = id.split("_");
        $("#hair_front .h_"+current_hairstyle+" .tinted").attr("fill","#"+id[0]);
        $("#hair_back .h_"+current_hairstyle+" .tinted").attr("fill","#"+id[1]);
        $("#facialhair g .tinted").attr("fill","#"+id[2]);
    });

    $("body").delegate(".facialhairs","click",function() {
        var id = $(this).attr("id");
        id = id.substr(2);
        $("#facialhair g").hide();
        $("#facialhair #f_"+id).show();
    });

    $("body").delegate(".clothesmenu","click",function() {
        var id = $(this).attr("id");
        id = id.substr(2);
        $("#clothes g").hide();
        $("#clothes #c_"+id).show();
    });

    $("body").delegate(".fabriccolors","click",function() {
        var id = $(this).attr("id");
        id = id.substr(2);
        current_fabriccolors = id;
        $("#clothes g .tinted").attr("fill","#"+id);
    });

    $("body").delegate(".backgroundcolors","click",function() {
        var id = $(this).attr("id");
        id = id.substr(2);
        current_backgroundcolors = id;
        $("#background").attr("fill","#"+id);
    });

    // $("body").delegate("#random","click",function() {
    //     random();
    // });

    // random();

})



// function random() {
//     var rand_skins = skins[Math.floor(Math.random()*skins.length)];
//     var rand_eyes = eyes[Math.floor(Math.random()*eyes.length)];
//     var rand_eyebrows = eyebrows[Math.floor(Math.random()*eyebrows.length)];
//     var rand_mouths = mouths[Math.floor(Math.random()*mouths.length)];
//     var rand_hairstyles = hairstyles[Math.floor(Math.random()*hairstyles.length)];
//     var rand_haircolors = haircolors[Math.floor(Math.random()*haircolors.length)];
//     var rand_facialhairs = facialhairs[Math.floor(Math.random()*facialhairs.length)];
//     var rand_clothes = clothesmenu[Math.floor(Math.random()*clothesmenu.length)];
//     var rand_fabriccolors = fabriccolors[Math.floor(Math.random()*fabriccolors.length)];
//     var rand_backgroundcolors = backgroundcolors[Math.floor(Math.random()*backgroundcolors.length)];
//     current_skincolor = rand_skins;
//     current_fabriccolors = rand_fabriccolors;
//     current_backgroundcolors = rand_backgroundcolors;
//     $("#skin #body").attr("fill","#"+rand_skins);
//     $("#eye g").hide();
//     $("#eye #e_"+rand_eyes).show();
//     $("#eyebrow g").hide();
//     $("#eyebrow #eb_"+rand_eyebrows).show();
//     $("#mouth g").hide();
//     $("#mouth #m_"+rand_mouths).show();
//     current_hairstyle = rand_hairstyles;
//     $("#hair_front g").hide();
//     $("#hair_back g").hide();
//     $("#hair_front .h_"+rand_hairstyles).show();
//     $("#hair_back .h_"+rand_hairstyles).show();
//     current_haircolor = rand_haircolors;
//     var color = current_haircolor;
//     color = color.split("_");
//     $("#hair_front .h_"+current_hairstyle+" .tinted").attr("fill","#"+color[0]);
//     $("#hair_back .h_"+current_hairstyle+" .tinted").attr("fill","#"+color[1]);
//     $("#facialhair g .tinted").attr("fill","#"+color[2]);
//     $("#facialhair g").hide();
//     $("#facialhair #f_"+rand_facialhairs).show();
//     $("#clothes g").hide();
//     $("#clothes #c_"+rand_clothes).show();
//     $("#clothes g .tinted").attr("fill","#"+rand_fabriccolors);
//     $("#background").attr("fill","#"+rand_backgroundcolors);
// }