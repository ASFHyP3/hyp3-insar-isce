FROM continuumio/miniconda3:4.7.12-alpine

ENV PATH=/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

USER 0
RUN apk add --no-cache bash && \
    rm /home/anaconda/.profile && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> /home/anaconda/.profile && \
    chown anaconda:anaconda /home/anaconda/.profile

USER 10151
SHELL ["bash", "-l", "-c"]
ENV PYTHONDONTWRITEBYTECODE=true
WORKDIR /home/anaconda/

RUN conda create -y -c conda-forge -n hyp3-inar-isce python=3.8 \
    boto3 gdal imageio lxml netCDF4 matplotlib numpy pillow \
    proj4 psycopg2 scipy six statsmodels && \
    conda clean -afy && \
    conda activate hyp3-inar-isce && \
    echo "conda activate hyp3-inar-isce" >> /home/anaconda/.profile

ARG S3_PYPI_HOST

RUN python -m pip install --no-cache-dir hyp3insarisce \
    --trusted-host "${S3_PYPI_HOST}" \
    --extra-index-url "http://${S3_PYPI_HOST}"

ENTRYPOINT ["conda", "run", "-n", "hyp3-inar-isce", "proc_insar_isce.py"]
CMD ["-v"]

# NOTE: Steps for building this container:
#    * make sure to set:
#       * --no-cache
#       * --build-arg S3_PYPI_HOST=${S3_PYPI_HOST}
#       * -t hyp3-insar-isce:$(python setup.py --version | tr -s + _)
#       * -t hyp3-insar-isce:latest

# NOTE: Steps for rsunning this container:
#    * mount the `.hyp3` dir to '/home/anaonda/.hyp3'
#       * should have at least `proc.cfg` in it
#       * needs .hyp3/lock and .hyp3/log dirs to exist and be witeable by the
#         container user -- easiest to chmod 777 them, but could play the uid
#         gid game
#   * mount something to /data/hyp3_workdir that is witeable by the container
#     user -- easiest to chmod 777 them, but could play the uid gid game
