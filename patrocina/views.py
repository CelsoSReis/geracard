import os
import io
import base64
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont, ImageOps
from django.core.files.base import ContentFile

def patrocinadores(request):
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip().upper()
        cidade = request.POST.get('cidade', '').strip().upper()
        
        foto_base64 = request.POST.get('foto_cortada')
        foto_upload = request.FILES.get('foto')

        try:
            # 1. Carregar a Moldura
            path_moldura = os.path.join(settings.BASE_DIR, 'static', 'img', 'moldura1.png')
            moldura = Image.open(path_moldura).convert("RGBA")
            largura_m, altura_m = moldura.size

            fundo_foto = Image.new("RGBA", moldura.size, (255, 255, 255, 0))
            draw_fundo = ImageDraw.Draw(fundo_foto)
            
            tamanho_circulo = 1030 
            pos_x = (largura_m - tamanho_circulo) // 2
            pos_y = 480 

            # Configuração das Fontes (carregadas antes para usar no fallback se necessário)
            try:
                font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'ARIALBD.TTF')
                font_nome = ImageFont.truetype(font_path, 70)
                font_cidade = ImageFont.truetype(font_path, 50)
                # Fonte maior para o nome dentro do círculo
                font_fallback = ImageFont.truetype(font_path, 100) 
            except:
                font_nome = font_cidade = font_fallback = ImageFont.load_default()

            # 2. Processar a Foto ou o Nome no Círculo
            if foto_base64 and len(foto_base64) > 10:
                format, imgstr = foto_base64.split(';base64,')
                foto_data = ContentFile(base64.b64decode(imgstr))
                foto_perfil = Image.open(foto_data).convert("RGBA")
                foto_perfil = ImageOps.fit(foto_perfil, (tamanho_circulo, tamanho_circulo), Image.LANCZOS)
                fundo_foto.paste(foto_perfil, (pos_x, pos_y))
            
            elif foto_upload:
                foto_perfil = Image.open(foto_upload).convert("RGBA")
                foto_perfil = ImageOps.fit(foto_perfil, (tamanho_circulo, tamanho_circulo), Image.LANCZOS)
                fundo_foto.paste(foto_perfil, (pos_x, pos_y))
            
            else:
                # CASO SEM FOTO: Círculo Branco + Nome no Centro
                cor_branca = (255, 255, 255, 255)
                draw_fundo.ellipse(
                    [pos_x, pos_y, pos_x + tamanho_circulo, pos_y + tamanho_circulo], 
                    fill=cor_branca
                )
                
                # Calcular posição central do texto dentro do círculo
                # Bbox retorna (left, top, right, bottom)
                bbox = draw_fundo.textbbox((0, 0), nome, font=font_fallback)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Centro do círculo
                centro_x = pos_x + (tamanho_circulo // 2) - (text_width // 2)
                centro_y = pos_y + (tamanho_circulo // 2) - (text_height // 2)
                
                # Desenha o nome em cor escura (Azul ou Preto) para dar contraste no branco
                draw_fundo.text((centro_x, centro_y), nome, font=font_fallback, fill=(30, 70, 230, 255))

            # 3. Sobreposição
            final = Image.alpha_composite(fundo_foto, moldura)
            draw = ImageDraw.Draw(final)

            # 4. Posicionamento do Texto nas Faixas Inferiores
            w_n = draw.textlength(nome, font=font_nome)
            draw.text(((largura_m - w_n) / 2, 1720), nome, font=font_nome, fill="white")

            w_c = draw.textlength(cidade, font=font_cidade)
            draw.text(((largura_m - w_c) / 2, 1815), cidade, font=font_cidade, fill="white")

            # 5. Salvar e Retornar
            byte_io = io.BytesIO()
            final.convert("RGB").save(byte_io, 'JPEG', quality=95)
            
            response = HttpResponse(byte_io.getvalue(), content_type="image/jpeg")
            response['Content-Disposition'] = f'attachment; filename="card_{nome}.jpg"'
            response.set_cookie("download_status", "concluido", max_age=30)
            return response

        except Exception as e:
            return HttpResponse(f"Erro: {e}")

    return render(request, 'patrocina.html')